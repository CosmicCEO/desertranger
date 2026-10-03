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

## Generated / original

- **Voices:** generated with Chatterbox (model `ResembleAI/chatterbox`, MIT licence). Output carries Resemble's inaudible Perth watermark. Voices are cloned only from Kokoro preset reference voices, never from a real person.
- **Reference voices:** Kokoro-82M (Apache-2.0), used as cloning references only; not shipped.
- **Bed, critters and radio FX:** original, synthesized with ffmpeg in this repo (`tools/audio/`, hand-off section 8).
- **Ambience bed and critters (`amb/`):** `amb-bed-01`, `amb-rattle-01`, `amb-truck-01`, `amb-crickets-01` are original, synthesized with ffmpeg (`tools/audio/make_ambience.py`, hand-off 8.3/8.4). No third-party material.
