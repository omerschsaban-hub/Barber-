from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class Stage(str,Enum): OBSERVE='observe'; UNDERSTAND='understand'; ACT='act'; MEASURE='measure'; EVALUATE='evaluate'; LEARN='learn'; STOP='stop'
@dataclass
class LoopPolicy:
    max_iterations:int=10; budget_limit:float=0.0; require_human_for_external_action:bool=True
@dataclass
class LoopState:
    iteration:int=0; stage:Stage=Stage.OBSERVE; status:str='paused'; evidence:list[dict]=field(default_factory=list)

def next_stage(state:LoopState,policy:LoopPolicy)->LoopState:
    if state.iteration>=policy.max_iterations: state.stage=Stage.STOP; state.status='completed'; return state
    order=[Stage.OBSERVE,Stage.UNDERSTAND,Stage.ACT,Stage.MEASURE,Stage.EVALUATE,Stage.LEARN]
    i=order.index(state.stage)
    if state.stage==Stage.LEARN: state.iteration+=1; state.stage=Stage.OBSERVE
    else: state.stage=order[i+1]
    return state

def gate_external_action(policy:LoopPolicy, approved:bool)->None:
    if policy.require_human_for_external_action and not approved: raise PermissionError('human approval required for external action')

AGENTS=('research','customer','engineering','experiment','analytics','ml','critic','strategy','orchestrator')
