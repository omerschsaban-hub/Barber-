import {NextRequest, NextResponse} from 'next/server';
import {cookies} from 'next/headers';
import {createHash} from 'node:crypto';
import {checkAndConsumeLlmRun, llmUsageMessage, type LlmUsagePlan} from '@/lib/llm-usage';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API ||
  (process.env.NODE_ENV === 'production'
    ? 'https://fabrient-engineering.onrender.com'
    : 'http://localhost:8000');

const MODEL = process.env.OPENAI_MODEL || (process.env.OPENAI_API_BASE ? 'gpt-5.5' : 'gpt-5.6');
const OPENAI_URL = `${(process.env.OPENAI_API_BASE || 'https://api.openai.com/v1').replace(/\/$/, '')}/responses`;
const BILLING_API = process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com';

const ALLOWED_OPERATIONS = new Set([
  '/v1/predict',
  '/v1/simulate',
  '/v1/calibrate',
  '/v1/uncertainty',
  '/v1/reverification',
  '/v1/next-experiment',
  '/v1/acceptance',
  '/v1/agents/run',
  '/v1/sim2real/run',
  '/v1/sim2real/compare',
  '/v1/final/risk',
  '/v1/system-identification',
]);

const INTENT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    operation: {
      type: 'string',
      enum: Array.from(ALLOWED_OPERATIONS),
    },
    payload: {type: 'object', additionalProperties: true},
    intent_summary: {type: 'string'},
    entity: {type: ['string', 'null']},
    resolved_dimensions_mm: {
      type: ['object', 'null'],
      additionalProperties: false,
      properties: {
        width: {type: ['number', 'null']},
        height: {type: ['number', 'null']},
        depth: {type: ['number', 'null']},
      },
      required: ['width', 'height', 'depth'],
    },
    evidence_sources: {
      type: 'array',
      items: {type: 'string'},
    },
    missing_information: {
      type: 'array',
      items: {type: 'string'},
    },
    confidence: {type: 'number'},
  },
  required: [
    'operation', 'payload', 'intent_summary', 'entity',
    'resolved_dimensions_mm', 'evidence_sources', 'missing_information', 'confidence',
  ],
} as const;

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function sanitizePayload(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const input = value as Record<string, unknown>;
  const output: Record<string, unknown> = {};
  for (const [key, raw] of Object.entries(input)) {
    if (key.length > 100) continue;
    if (typeof raw === 'string') output[key] = raw.slice(0, 10000);
    else if (typeof raw === 'number' && Number.isFinite(raw)) output[key] = raw;
    else if (typeof raw === 'boolean' || raw === null) output[key] = raw;
    else if (Array.isArray(raw)) output[key] = raw.slice(0, 100).map(v =>
      typeof v === 'string' ? v.slice(0, 2000) : v
    );
    else if (typeof raw === 'object') output[key] = raw;
  }
  return output;
}

async function resolveIntent(
  naturalLanguage: string,
  requestedOperation: string | undefined,
  suppliedPayload: Record<string, unknown>,
) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY is not configured on the server.');
  }

  const forced = requestedOperation && ALLOWED_OPERATIONS.has(requestedOperation)
    ? requestedOperation
    : null;

  const instructions = `You are Fabrient's engineering intent layer. You sit ABOVE deterministic physics/math and ML models.

Your job is semantic understanding only: understand what the human means, resolve named products/devices/materials when possible, and produce a strict machine-readable plan for the existing engineering engine.

Rules:
- Never invent measurements, tolerances, material properties, or product dimensions.
- If a named physical product is mentioned (for example an iPhone model), use web search when exact current dimensions are needed. Prefer manufacturer/primary sources; otherwise use reputable technical sources and record their URLs in evidence_sources.
- If web evidence is unavailable or conflicting, leave the affected dimension null and put the problem in missing_information. Do NOT guess.
- Preserve explicit user-supplied numeric values exactly. The LLM must never silently replace them.
- Do not perform engineering calculations yourself. Deterministic physics and the existing ML models remain authoritative for calculations, calibration, uncertainty, risk, and acceptance.
- ML may only learn from real observations already supplied to the engineering service; synthetic values are never training evidence.
- Choose only one of the allowed operations.
- If an operation requires information that is genuinely absent, still return the best semantic interpretation and list missing_information rather than fabricating values.
- JSON output must match the supplied schema exactly.
${forced ? `The UI explicitly requested operation ${forced}. You MUST keep that operation.` : 'Infer the operation from the human request.'}

Allowed operations: ${Array.from(ALLOWED_OPERATIONS).join(', ')}.`;

  const input = JSON.stringify({
    human_request: naturalLanguage.slice(0, 12000),
    requested_operation: requestedOperation || null,
    supplied_payload: suppliedPayload,
  });

  const needsWebSearch = Boolean(naturalLanguage.trim()) &&
    /iphone|ipad|macbook|pixel|galaxy|arduino|raspberry pi|stm32|esp32|pcb|board|printer|device|phone|laptop|tablet/i.test(naturalLanguage);

  const body: Record<string, unknown> = {
    model: MODEL,
    instructions,
    input,
    store: false,
    temperature: 0,
    text: {
      format: {
        type: 'json_schema',
        name: 'fabrient_engineering_intent',
        strict: true,
        schema: INTENT_SCHEMA,
      },
    },
  };
  if (needsWebSearch) {
    body.tools = [{type: 'web_search'}];
    body.include = ['web_search_call.action.sources'];
  }

  const response = await fetch(OPENAI_URL, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(45_000),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.error?.message || `OpenAI request failed (${response.status})`;
    throw new Error(detail);
  }

  const raw = typeof data?.output_text === 'string'
    ? data.output_text
    : data?.output?.find((item: any) => item?.type === 'message')?.content?.find((c: any) => c?.type === 'output_text')?.text;
  if (!raw) throw new Error('OpenAI returned no structured intent.');

  const parsed = JSON.parse(raw);
  if (!ALLOWED_OPERATIONS.has(parsed.operation)) throw new Error('LLM selected an unsupported engineering operation.');
  parsed.payload = sanitizePayload(parsed.payload);

  // The LLM is never allowed to overwrite explicit numeric input.
  for (const [key, value] of Object.entries(suppliedPayload)) {
    if (isFiniteNumber(value)) parsed.payload[key] = value;
  }

  return parsed;
}

async function runEngineering(operation: string, payload: Record<string, unknown>, requestId: string) {
  const response = await fetch(`${ENGINE}${operation}`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-fabrient-request-id': requestId,
      'x-fabrient-orchestration': 'llm+deterministic+ml',
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(120_000),
  });
  const body = await response.json().catch(() => ({}));
  return {ok: response.ok, status: response.status, body};
}

async function getPlanAndUsageKey() {
  const token = (await cookies()).get('fabrient_session')?.value;
  if (!token) return null;
  try {
    const response = await fetch(`${BILLING_API.replace(/\/$/, '')}/billing/access`, {
      headers: {Authorization: `Bearer ${token}`},
      cache: 'no-store',
      signal: AbortSignal.timeout(5_000),
    });
    if (!response.ok) return null;
    const body = await response.json().catch(() => ({}));
    const plan = body?.plan;
    return {
      key: createHash('sha256').update(token).digest('hex'),
      plan: (plan === 'hobbyist' || plan === 'startup' || plan === 'enterprise' ? plan : 'free') as LlmUsagePlan,
    };
  } catch {
    return null;
  }
}

export async function POST(request: NextRequest) {
  const requestId = request.headers.get('x-fabrient-request-id') || crypto.randomUUID();
  try {
    const access = await getPlanAndUsageKey();
    if (!access) return NextResponse.json({error: 'Sign in before using the engineering copilot.'}, {status: 401});
    const body = await request.json();
    const naturalLanguage = typeof body?.naturalLanguage === 'string' ? body.naturalLanguage : '';
    const requestedOperation = typeof body?.operation === 'string' ? body.operation : undefined;
    const suppliedPayload = sanitizePayload(body?.payload);
    const execute = body?.execute !== false;

    if (!naturalLanguage && !requestedOperation) {
      return NextResponse.json({error: 'Provide naturalLanguage or an operation.'}, {status: 400});
    }
    if (requestedOperation && !ALLOWED_OPERATIONS.has(requestedOperation)) {
      return NextResponse.json({error: 'Unsupported engineering operation.'}, {status: 400});
    }

    const usage = checkAndConsumeLlmRun(access.key, access.plan);
    if (!usage.allowed) {
      const response = NextResponse.json({
        status: 'usage_limited',
        error: usage.reason === 'monthly_limit'
          ? `You have used all ${usage.limit} free AI runs for this month.`
          : 'You are using the copilot quickly. Please wait a few minutes and try again.',
        plan: access.plan,
        usage: {used: usage.used, limit: usage.limit, reset_at: new Date(usage.resetAt).toISOString()},
      }, {status: 429});
      if (usage.retryAfterSeconds) response.headers.set('Retry-After', String(usage.retryAfterSeconds));
      return response;
    }

    const intent = await resolveIntent(naturalLanguage || requestedOperation!, requestedOperation, suppliedPayload);

    const layers = {
      llm: {model: MODEL, role: 'intent/entity resolution'},
      deterministic: {role: 'authoritative physics/geometry/rules'},
      ml: {role: 'calibration/system identification from real observations only'},
    };

    if (!execute || intent.missing_information.length > 0) {
      return NextResponse.json({
        status: intent.missing_information.length ? 'needs_input' : 'planned',
        request_id: requestId,
        intent,
        layers,
        usage: {used: usage.used, limit: usage.limit, message: llmUsageMessage(access.plan, usage.used, usage.limit)},
      });
    }

    const result = await runEngineering(intent.operation, intent.payload, requestId);
    if (!result.ok) {
      return NextResponse.json({
        status: 'engineering_error',
        request_id: requestId,
        intent,
        layers,
        engineering: result.body,
        usage: {used: usage.used, limit: usage.limit, message: llmUsageMessage(access.plan, usage.used, usage.limit)},
      }, {status: result.status});
    }

    return NextResponse.json({
      status: 'completed',
      request_id: requestId,
      intent,
      layers,
      engineering: result.body,
      usage: {used: usage.used, limit: usage.limit, message: llmUsageMessage(access.plan, usage.used, usage.limit)},
    });
  } catch (error: any) {
    return NextResponse.json({
      status: 'failed',
      request_id: requestId,
      error: error?.message || 'Engineering orchestration failed',
    }, {status: 500});
  }
}
