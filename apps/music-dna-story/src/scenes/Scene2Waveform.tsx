import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const GOLD = '#D4AF37';

interface WaveformProps {
  color: string;
  frequency: number;
  amplitude: number;
  phase: number;
  opacity: number;
  strokeWidth: number;
  yOffset: number;
  noiseScale: number;
  frame: number;
  width: number;
  height: number;
}

const Waveform: React.FC<WaveformProps> = ({
  color,
  frequency,
  amplitude,
  phase,
  opacity,
  strokeWidth,
  yOffset,
  noiseScale,
  frame,
  width,
  height,
}) => {
  const points = 200;
  const pathData = Array.from({ length: points }, (_, i) => {
    const x = (i / (points - 1)) * width;
    const t = (i / (points - 1)) * Math.PI * 2 * frequency;
    const noise = Math.sin(t * 0.5 + frame * 0.03) * noiseScale;
    const y = height / 2 + yOffset + Math.sin(t + phase + frame * 0.04) * amplitude + noise;
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  return (
    <path
      d={pathData}
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      opacity={opacity}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  );
};

export const Scene2Waveform: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const enterProgress = spring({ fps, frame, config: { damping: 50, stiffness: 60 }, durationInFrames: 40 });
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const wave1Opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const wave2Opacity = interpolate(frame, [10, 30], [0, 0.65], { extrapolateRight: 'clamp' });
  const wave3Opacity = interpolate(frame, [20, 40], [0, 0.35], { extrapolateRight: 'clamp' });

  const labelOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateRight: 'clamp' });
  const labelY = interpolate(frame, [40, 60], [20, 0], { extrapolateRight: 'clamp' });

  const titleOpacity = interpolate(frame, [15, 40], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{ backgroundColor: '#0a0a0a', opacity: exitOpacity }}
    >
      {/* Background grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }}
      />

      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 60,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 13,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.3)',
            letterSpacing: '5px',
            textTransform: 'uppercase',
            marginBottom: 12,
          }}
        >
          Frequency Signature Analysis
        </div>
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 36,
            fontWeight: 700,
            color: '#ffffff',
            letterSpacing: '-1px',
          }}
        >
          Three Layers of Sound
        </div>
      </div>

      {/* SVG Waveforms */}
      <svg
        width={width}
        height={height}
        style={{ position: 'absolute', inset: 0 }}
      >
        {/* Sub-bass Log Drum — Gold, wide, slow */}
        <Waveform
          color={GOLD}
          frequency={2.5}
          amplitude={interpolate(enterProgress, [0, 1], [0, 90])}
          phase={0}
          opacity={wave1Opacity}
          strokeWidth={3.5}
          yOffset={20}
          noiseScale={15}
          frame={frame}
          width={width}
          height={height}
        />

        {/* Mid-range percussion — White, medium */}
        <Waveform
          color="#ffffff"
          frequency={4.5}
          amplitude={interpolate(enterProgress, [0, 1], [0, 50])}
          phase={1.2}
          opacity={wave2Opacity}
          strokeWidth={2}
          yOffset={-15}
          noiseScale={8}
          frame={frame}
          width={width}
          height={height}
        />

        {/* High freq synth — White, tight */}
        <Waveform
          color="#ffffff"
          frequency={7}
          amplitude={interpolate(enterProgress, [0, 1], [0, 28])}
          phase={2.4}
          opacity={wave3Opacity}
          strokeWidth={1.2}
          yOffset={10}
          noiseScale={4}
          frame={frame}
          width={width}
          height={height}
        />
      </svg>

      {/* Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: 80,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          gap: 60,
          opacity: labelOpacity,
          transform: `translateY(${labelY}px)`,
        }}
      >
        {[
          { color: GOLD, label: 'Log Drum Sub-Bass', freq: '20–60 Hz' },
          { color: 'rgba(255,255,255,0.65)', label: 'Percussion Layer', freq: '200–2k Hz' },
          { color: 'rgba(255,255,255,0.35)', label: 'Piano Synth', freq: '2k–8k Hz' },
        ].map(({ color, label, freq }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 32,
                height: 2,
                backgroundColor: color,
                borderRadius: 1,
              }}
            />
            <div>
              <div
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#ffffff',
                  letterSpacing: '0.5px',
                }}
              >
                {label}
              </div>
              <div
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 11,
                  color: 'rgba(255,255,255,0.35)',
                  letterSpacing: '1px',
                }}
              >
                {freq}
              </div>
            </div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
