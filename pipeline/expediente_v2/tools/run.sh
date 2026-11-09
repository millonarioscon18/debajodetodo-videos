#!/bin/bash
# run.sh name port outname
cd /home/claude/miedo/v2/$1
N=$(python3 -c "import json,math;print(math.ceil(json.load(open('timeline.json'))['dur']*24))"); H=$((N/2))
rm -rf frames; mkdir -p frames
node /home/claude/engine/render.js 0 $H 24 full $2 > ra.log 2>&1 &
node /home/claude/engine/render.js $H $N 24 full $2 > rb.log 2>&1 &
wait
ffmpeg -loglevel error -y -framerate 24 -i frames/%05d.jpg -i mix.wav -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart $3 && echo "DONE $1 $(ls frames | wc -l)/$N" >> /home/claude/miedo/v2/render_status.txt
