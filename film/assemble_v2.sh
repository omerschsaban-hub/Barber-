#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p work_v2 output

make_still () {
  local name="$1"; local seconds="$2"
  ffmpeg -y -loop 1 -i "assets/${name}.jpg" -t "$seconds" -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0007,1.07)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$((seconds*24)):s=1920x1080:fps=24,format=yuv420p" -an "work_v2/${name}.mp4" >/dev/null 2>&1
}

# Timeline: 8 + 12 + 11 + 12 + 11 + 12 + 12 + 16 + 20 + 6 = exactly 120 seconds.
ffmpeg -y -i assets/00_opening.mp4 -t 8 -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p" -an work_v2/00_opening.mp4 >/dev/null 2>&1
make_still 02_workspace 12
make_still 06_assembly_sourcing_cost 11
make_still 01_cad_enclosure 12
make_still 03_failure_fix 11
make_still 04_physical_evidence 12
make_still 07_ml_analytics 12
make_still 08_human_agent_mcp 16
make_still 09_manufacturing_package 20
make_still 05_release 6

cat > work_v2/concat.txt <<'EOF'
file '00_opening.mp4'
file '02_workspace.mp4'
file '06_assembly_sourcing_cost.mp4'
file '01_cad_enclosure.mp4'
file '03_failure_fix.mp4'
file '04_physical_evidence.mp4'
file '07_ml_analytics.mp4'
file '08_human_agent_mcp.mp4'
file '09_manufacturing_package.mp4'
file '05_release.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i work_v2/concat.txt -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 24 work_v2/picture.mp4 >/dev/null 2>&1

# The generated reading is 134.96s; 1.125x preserves clarity while fitting the exact 120s visual arc.
ffmpeg -y -i assets/revised_narration.wav -filter:a "atempo=1.125,volume=1.0" -ar 48000 work_v2/narration_fit.wav >/dev/null 2>&1
ffmpeg -y -stream_loop -1 -i assets/score.wav -t 120 -filter:a "afade=t=out:st=116:d=4,volume=0.16" -ar 48000 work_v2/score_fit.wav >/dev/null 2>&1
ffmpeg -y -i work_v2/picture.mp4 -i work_v2/narration_fit.wav -i work_v2/score_fit.wav -filter_complex "[1:a]acompressor=threshold=-18dB:ratio=2:attack=20:release=250[n];[2:a]sidechaincompress=threshold=0.02:ratio=5:attack=20:release=350:makeup=1[m];[n][m]amix=inputs=2:duration=first:dropout_transition=2[a]" -map 0:v:0 -map "[a]" -t 120 -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -movflags +faststart output/fabrient_launch_demo_improved.mp4 >/dev/null 2>&1
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -show_entries format=duration -of default=noprint_wrappers=1 output/fabrient_launch_demo_improved.mp4
