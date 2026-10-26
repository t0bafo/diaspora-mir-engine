import './index.css';
import { Composition } from 'remotion';
import { MusicDNAComposition } from './Composition';

// 90s × 30fps = 2700 frames
// Each TransitionSeries.Transition with out-in 20 frames adds 20 frames per transition
// 4 transitions × 20 = 80 extra frames → total 2780
const TOTAL_FRAMES = 2780;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MusicDNA"
      component={MusicDNAComposition}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
