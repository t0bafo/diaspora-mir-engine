# Deep MIR Analysis Findings

## Artist Signature Analysis
The top artists in the dataset show distinctive "Groove Signatures":

| artist      |   complexity |   syncopation |   pulse_clarity |   danceability |     bpm |
|:------------|-------------:|--------------:|----------------:|---------------:|--------:|
| Kcee        |     0.498525 |      0.383975 |        0.75855  |       0.608725 | 109.72  |
| Seyi Vibez  |     0.75714  |      0.38854  |        0.7541   |       0.60786  | 112.628 |
| Unknown     |     0.7556   |      0.318078 |        0.688544 |       0.540344 | 116.989 |
| Davido      |     0.627814 |      0.350457 |        0.665057 |       0.539214 | 108.577 |
| Khaid       |     0.703533 |      0.400633 |        0.6245   |       0.534933 | 111.067 |
| Tems        |     0.687467 |      0.363033 |        0.6478   |       0.533867 | 106.577 |
| Tekno       |     0.608125 |      0.30755  |        0.679975 |       0.531    | 109.975 |
| Tyla        |     0.52084  |      0.39746  |        0.6133   |       0.52694  | 107.2   |
| Llona       |     0.8555   |      0.3638   |        0.631    |       0.524125 | 137.238 |
| Ayra Starr  |     0.7199   |      0.3769   |        0.615325 |       0.51995  | 108.695 |
| Burna Boy   |     0.656645 |      0.360909 |        0.621027 |       0.516982 | 112.501 |
| Rema        |     0.673443 |      0.363486 |        0.617571 |       0.515943 | 106.859 |
| Wizkid      |     0.618114 |      0.391957 |        0.577614 |       0.503357 | 107.137 |
| Omah Lay    |     0.6334   |      0.358675 |        0.58885  |       0.496775 | 106.24  |
| Fireboy DML |     0.625167 |      0.306133 |        0.5663   |       0.462233 | 105.35  |

## Natural Rhythmic Clusters
We identified 3 natural "states" of rhythm in this collection:
|   cluster |   syncopation |   pulse_clarity |   complexity |   danceability |   track_count |
|----------:|--------------:|----------------:|-------------:|---------------:|--------------:|
|         0 |      0.348173 |        0.68897  |     0.571639 |       0.552649 |            83 |
|         1 |      0.359649 |        0.508888 |     0.667302 |       0.449195 |            41 |
|         2 |      0.358952 |        0.698664 |     0.847945 |       0.562779 |            33 |

### Cluster Interpretation:
- **Cluster High-Danceability**: Likely Amapiano and driving Afrobeats hits. High Pulse Clarity + High Syncopation.
- **Cluster Vibe**: Lower pulse clarity, moderate syncopation. The "chill" Afrobeats sound.
- **Cluster Complex**: High complexity, varying pulse. Experimental or highly polyrhythmic tracks.

## Top 10 High-Syncopation Tracks
| artist                 | file_name                                                       |   syncopation |
|:-----------------------|:----------------------------------------------------------------|--------------:|
| Shallipopi             | Shallipopi - Laho.mp3                                           |        0.519  |
| Tyla                   | Tyla - PUSH 2 START.mp3                                         |        0.4984 |
| Tyla                   | Tyla - PUSH 2 START (Official Audio).mp3                        |        0.4963 |
| ODUMODUBLVCK           | ODUMODUBLVCK - NOT ALL THAT (OFFICIAL VIDEO).mp3                |        0.4757 |
| ODUMODUBLVCK           | ODUMODUBLVCK - NOT ALL THAT.mp3                                 |        0.4712 |
| Wizkid                 | Wizkid - Piece of My Heart (Lyrics) ft. Brent Faiyaz.mp3        |        0.4541 |
| Wizkid                 | Wizkid - Piece Of My Heart (Audio) ft. Brent Faiyaz.mp3         |        0.4534 |
| Brent Faiyaz           | Brent Faiyaz - Piece of My Heart.mp3                            |        0.4508 |
| Kcee                   | Kcee - Motor ft Kanika Kapoor.mp3                               |        0.4501 |
| Kaestyle & Kizz Daniel | Kaestyle & Kizz Daniel - My Dealer (Remix) (Official Audio).mp3 |        0.4468 |

## Top 10 Most Danceable Tracks (v1.2.1 Formula)
| artist        | file_name                                                              |   danceability |
|:--------------|:-----------------------------------------------------------------------|---------------:|
| Kcee          | Kcee - Motor ft Kanika Kapoor.mp3                                      |         0.665  |
| Seyi Vibez    | Seyi Vibez - HAPPY SONG (Official Audio).mp3                           |         0.6626 |
| Kcee          | Kcee - Motor feat. Kanika Kapoor (Official Audio).mp3                  |         0.6546 |
| Seyi Vibez    | Seyi Vibez - MARIO KART.mp3                                            |         0.6488 |
| Rema          | Rema - OZEBA (Lyric Visualizer).mp3                                    |         0.6485 |
| Asake         | Asake - WHY LOVE (Official Video).mp3                                  |         0.648  |
| Seyi Vibez    | Seyi Vibez - MARIO KART (Official Audio).mp3                           |         0.6478 |
| TitoM & Yuppe | TitoM & Yuppe - Tshwala Bam [Feat. S.N.E & EeQue] (Official Audio).mp3 |         0.6409 |
| ODUMODUBLVCK  | ODUMODUBLVCK - NOT ALL THAT.mp3                                        |         0.6201 |
| Mayorkun      | Mayorkun - Reason 2 Japa.mp3                                           |         0.6172 |

---
*Generated by deep_analysis.py*
