# Audio credits

Every third-party sound in `desertranger/audio/` must be **CC0 1.0** and has a row below.

## Third-party files (CC0 only)

| file | source page URL | direct file URL | author | license | retrieved (CT) | changes |
|---|---|---|---|---|---|---|
| dice/dice-shake-01.mp3 | https://kenney.nl/assets/casino-audio | https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip (`Audio/dice-shake-1.ogg` inside the zip) | Kenney Vleugels (Kenney.nl), Casino Audio 1.1 | CC0 1.0 | 2026-10-03 | trimmed to 0.7 s, 120 ms fade-out, mono, -20 LUFS, MP3 64 kbps |
| dice/dice-clatter-01.mp3 | https://kenney.nl/assets/casino-audio | https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip (`Audio/die-throw-1.ogg` inside the zip) | Kenney Vleugels (Kenney.nl), Casino Audio 1.1 | CC0 1.0 | 2026-10-03 | mono, 40 ms fade-out, -18 LUFS, MP3 64 kbps |
| dice/dice-clatter-02.mp3 | https://kenney.nl/assets/casino-audio | https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip (`Audio/die-throw-2.ogg` inside the zip) | Kenney Vleugels (Kenney.nl), Casino Audio 1.1 | CC0 1.0 | 2026-10-03 | mono, 40 ms fade-out, -18 LUFS, MP3 64 kbps |
| dice/dice-clatter-03.mp3 | https://kenney.nl/assets/casino-audio | https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip (`Audio/die-throw-3.ogg` inside the zip) | Kenney Vleugels (Kenney.nl), Casino Audio 1.1 | CC0 1.0 | 2026-10-03 | mono, 40 ms fade-out, -18 LUFS, MP3 64 kbps |
| dice/dice-clatter-04.mp3 | https://kenney.nl/assets/casino-audio | https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip (`Audio/die-throw-4.ogg` inside the zip) | Kenney Vleugels (Kenney.nl), Casino Audio 1.1 | CC0 1.0 | 2026-10-03 | mono, 40 ms fade-out, -18 LUFS, MP3 64 kbps |
| amb/amb-crow-01.mp3 | https://freesound.org/people/TheKingOfGeeks360/sounds/860982/ | https://cdn.freesound.org/previews/860/860982_15895934-hq.mp3 | TheKingOfGeeks360 (Freesound), "Corvids - American Crow, Single" | CC0 1.0 (license box on the page reads "Creative Commons 0", checked 2026-10-03) | 2026-10-03 | excerpt 0.15-0.75 s of the public hq preview, afftdn noise reduction, fades, mono, -26 LUFS, 64 kbps MP3 |
| amb/amb-coyote-01.mp3 | https://freesound.org/people/Gerent/sounds/558725/ | https://cdn.freesound.org/previews/558/558725_556505-hq.mp3 | Gerent (Freesound), "dogs-howling-yelping-distance-far-04.wav" (tagged coyote; uploader's description: coyotes yipping and howling at night) | CC0 1.0 (license box on the page reads "Creative Commons 0", checked 2026-10-03) | 2026-10-03 | excerpt 0.45-2.30 s of the public hq preview, afftdn noise reduction, fades, mono, -26 LUFS, 64 kbps MP3 |
| amb/amb-hawk-01.mp3 | https://freesound.org/people/craigsmith/sounds/479610/ | https://cdn.freesound.org/previews/479/479610_2524442-hq.mp3 | craigsmith (Freesound), "R30-34-Red Tailed Hawk.wav" | CC0 1.0 (license box on the page reads "Creative Commons 0", checked 2026-10-03) | 2026-10-03 | excerpt 7.40-9.30 s of the public hq preview, afftdn noise reduction, fades, mono, -26 LUFS, 64 kbps MP3 |

## Generated / original

- **Voices:** generated with Chatterbox (model `ResembleAI/chatterbox`, MIT licence). Output carries Resemble's inaudible Perth watermark. Voices are cloned only from Kokoro preset reference voices, never from a real person.
- **Reference voices:** Kokoro-82M (Apache-2.0), used as cloning references only; not shipped.
- **Bed, critters and radio FX:** original, synthesized with ffmpeg in this repo (`tools/audio/`, hand-off section 8).
- **Ambience bed and critters (`amb/`):** `amb-bed-01`, `amb-rattle-01`, `amb-truck-01`, `amb-crickets-01` are original, synthesized with ffmpeg (`tools/audio/make_ambience.py`, hand-off 8.3/8.4). No third-party material.
