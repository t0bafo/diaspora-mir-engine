import React from 'react';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { Scene1Hero } from './scenes/Scene1Hero';
import { Scene2Waveform } from './scenes/Scene2Waveform';
import { Scene3SplitScreen } from './scenes/Scene3SplitScreen';
import { Scene4Constellation } from './scenes/Scene4Constellation';
import { Scene5Outro } from './scenes/Scene5Outro';
import rawData from './data.json';
import type { MusicDNAData } from './types';

const data = rawData as MusicDNAData;

// 90 seconds at 30fps = 2700 frames
// Scene durations (frames):
//   Scene 1: 450  (15s)
//   Scene 2: 600  (20s)
//   Scene 3: 450  (15s)
//   Scene 4: 600  (20s)
//   Scene 5: 600  (20s)
// 4 transitions × 20 frames each = 80 extra → total 2780

const TRANSITION_FRAMES = 20;

export const MusicDNAComposition: React.FC = () => {
  const allTracks = data.all_tracks;

  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={450}>
        <Scene1Hero />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
      />

      <TransitionSeries.Sequence durationInFrames={600}>
        <Scene2Waveform />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
      />

      <TransitionSeries.Sequence durationInFrames={450}>
        <Scene3SplitScreen />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
      />

      <TransitionSeries.Sequence durationInFrames={600}>
        <Scene4Constellation tracks={allTracks} />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
      />

      <TransitionSeries.Sequence durationInFrames={600}>
        <Scene5Outro />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
