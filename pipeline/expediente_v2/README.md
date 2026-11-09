# Expediente Oscuro · formato v2 (cartoon) — cómo montar un vídeo

## Instalar en una sesión nueva
```bash
git clone https://github.com/millonarioscon18/debajodetodo-videos /tmp/dtv
mkdir -p /home/claude/engine /home/claude/miedo/v2
cp -r /tmp/dtv/pipeline/expediente_v2/engine/* /home/claude/engine/
cp /tmp/dtv/pipeline/expediente_v2/miedo/music.py /home/claude/miedo/
cp -r /tmp/dtv/pipeline/expediente_v2/tools /home/claude/miedo/v2/
pip install --break-system-packages numpy scipy
npm i -g playwright && npx playwright install chromium   # si falta
```
Las rutas están fijas a `/home/claude/engine` y `/home/claude/miedo`.

## Pasos para un vídeo (carpeta /home/claude/miedo/v2/NOMBRE)
1. **Guion** `parts.txt`: una línea por frase, con el formato `CÓDIGO|texto`.
   - Códigos: `N` (narrador Bruno), `D` (David), `A` (Alberto), `G` (Diego).
   - Entre 150 y 190 palabras de narrador dan un vídeo de 75–90 s.
   - Gancho en la primera frase; termina con una pregunta.
2. **ElevenLabs** (un flow por vídeo con `creative_create_flow`):
   - **Imágenes:** entre 11 y 13 nodos `image-generation`, modelo `bytedance-seedream-5-lite`, `{"aspect_ratio":"9:16","resolution":"2K"}`, `generations_count` 1 (unos 212 créditos cada una). Todos los prompts empiezan con:
     `Vertical 2D cartoon illustration in the style of a modern adult animated TV series, clean bold black outlines, flat colors with soft cel shading, expressive stylized characters.` y terminan con `Polished professional animation key frame. No text.`
   - **Clip del gancho:** nodo `video-generation` con `kling-2.5-turbo`, `{"duration_secs":5,"aspect_ratio":"9:16","negative_prompt":"realistic, photo, live action, text, distorted faces"}`, `connect_from` la imagen 01 (unos 2.121 créditos).
   - **Narrador:** `creative_generate_speech`, voz Bruno `bc3ewLiLNTrAqPzePbTH`, `eleven_v4`, `generations_count` 1. Va todo el texto N en una sola toma, con etiquetas `[whispering] [dramatic, intense] [low, ominous] [pause] [long pause]` y `[pause]` entre frases (unos 1.200–1.300 créditos).
   - **Personajes:** una llamada por frase, `generations_count` 1. Voces:
     - David `Nh2zY9kknu6z4pZy6FhD` (joven, castellano)
     - Alberto `l1zE9xgNpUTaQCZzpNJa` (adulto serio)
     - Diego `hLWSpwRIXvafYWP2GPET`
     - Sara Martin `gD1IexrzCvsXPHUuT0s3` (mujer)
     - Johnny The Rogue `HMCmDsbKeaSZp5LMOYKR` (villano)
   - Descargar los `content_url` con curl:
     - `cimg/01..NN.png`, convertidas a jpg con `ffmpeg -q:v 2`
     - `aud/N.mp3` y `aud/D1.mp3`, `A1.mp3`, `A2.mp3`… (numeradas en orden de aparición)
     - `clip.mp4`, sacando los fotogramas con `ffmpeg -i clip.mp4 -q:v 2 clip/%04d.jpg` (121 frames)
3. **Componer la voz:** `python3 ../tools/compose.py .` genera `vo.wav` y `timeline.json`. Corta al narrador en sus pausas e intercala a los personajes.
4. **Planos:** copia `v2engine/slides.js`, `index.html`, `engine/hud.js` y `engine/fonts` a la carpeta. Escribe `shots.json` (mira `ejemplos/`):
   - `at`: el número de línea o `{l, w, d}` (línea, palabra, desfase).
   - `move`: in, out, push, panL, panR, panU o panD.
   - `shake`.
   - `fx`: flicker, glitchy o red.
   - `tr`: fade, glitch, flash o black.
   - También admite `chapters`, `accent`, `cards`, `pulses` y `flashes`.
5. **Audio:** `sfx.json` lleva los efectos con el formato `[tipo, línea, palabra, ganancia]`. Los tipos son boom, boomhi, heart, riser, thud, stamp, blips, wind y slide. Después ejecuta `python3 audio.py`, que genera `mix.wav` con música original y la voz por encima.
6. **Render:** `python3 -m http.server PUERTO &`, después `node /home/claude/engine/jscheck.js PUERTO` (tiene que devolver `ready true`) y luego `tools/run.sh NOMBRE PUERTO salida.mp4`. Con 2 núcleos tarda unos 15 minutos.
   - Si el mp4 pasa de 95 MB, vuelve a codificarlo con `-crf 23`, porque GitHub no admite archivos de más de 100 MB.
   - Nunca hagas dos codificaciones a la vez sobre el mismo archivo.
7. **Publicar:** sube el mp4 a `expediente/` en este repositorio. La URL pública es `https://raw.githubusercontent.com/millonarioscon18/debajodetodo-videos/main/expediente/ARCHIVO.mp4`, que es la que se usa en Metricool.

Coste aproximado por vídeo: entre 6.500 y 7.000 créditos.
