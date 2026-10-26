import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const GOLD = '#D4AF37';
const SPOTIFY_DANCEABILITY = 0.41;
const OUR_DANCEABILITY = 0.6409;

const CountUp: React.FC<{
  from: number;
  to: number;
  startFrame: number;
  durationFrames: number;
  decimals?: number;
  color: string;
  label: string;
  fps: number;
}> = ({ from, to, startFrame, durationFrames, decimals = 2, color, label, fps }) => {
  const frame = useCurrentFrame();
  const progress = spring({
    fps,
    frame: Math.max(0, frame - startFrame),
    config: { damping: 40, stiffness: 80 },
    durationInFrames: durationFrames,
  });
  const value = interpolate(progress, [0, 1], [from, to]);

  return (
    <div style={{ textAlign: 'center' }}>
      <div
        style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: 72,
          fontWeight: 700,
          color,
          letterSpacing: '-2px',
          lineHeight: 1,
        }}
      >
        {value.toFixed(decimals)}
      </div>
      <div
        style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: 14,
          fontWeight: 400,
          color: 'rgba(255,255,255,0.5)',
          letterSpacing: '3px',
          textTransform: 'uppercase',
          marginTop: 8,
        }}
      >
        {label}
      </div>
    </div>
  );
};

export const Scene1Hero: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  const titleY = interpolate(frame, [0, 30], [30, 0], { extrapolateRight: 'clamp' });

  const artistOpacity = interpolate(frame, [15, 45], [0, 1], { extrapolateRight: 'clamp' });
  const artistY = interpolate(frame, [15, 45], [20, 0], { extrapolateRight: 'clamp' });

  const scoreRowOpacity = interpolate(frame, [45, 75], [0, 1], { extrapolateRight: 'clamp' });

  const dividerWidth = interpolate(frame, [60, 100], [0, 1], { extrapolateRight: 'clamp' });

  const vsOpacity = interpolate(frame, [80, 110], [0, 1], { extrapolateRight: 'clamp' });

  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0a0a0a',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: exitOpacity,
      }}
    >
      {/* Subtle grid lines */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(212,175,55,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(212,175,55,0.03) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Hero content */}
      <div style={{ position: 'relative', textAlign: 'center', zIndex: 2, width: '100%', padding: '0 80px' }}>
        {/* Track title */}
        <div
          style={{
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
            fontFamily: 'Inter, sans-serif',
            fontSize: 56,
            fontWeight: 800,
            color: '#ffffff',
            letterSpacing: '-1px',
            marginBottom: 8,
          }}
        >
          TitoM &amp; Yuppe
        </div>

        {/* Song name with gold accent */}
        <div
          style={{
            opacity: artistOpacity,
            transform: `translateY(${artistY}px)`,
            fontFamily: 'Inter, sans-serif',
            fontSize: 84,
            fontWeight: 900,
            color: GOLD,
            letterSpacing: '-3px',
            lineHeight: 1,
            marginBottom: 16,
          }}
        >
          Tshwala Bam
        </div>

        {/* Genre tag */}
        <div
          style={{
            opacity: artistOpacity,
            transform: `translateY(${artistY}px)`,
            display: 'inline-block',
            fontFamily: 'Inter, sans-serif',
            fontSize: 13,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.4)',
            letterSpacing: '4px',
            textTransform: 'uppercase',
            border: '1px solid rgba(255,255,255,0.15)',
            padding: '6px 18px',
            borderRadius: 3,
            marginBottom: 60,
          }}
        >
          Amapiano · 111.98 BPM
        </div>

        {/* Divider */}
        <div style={{ opacity: scoreRowOpacity, marginBottom: 50 }}>
          <div
            style={{
              height: 1,
              background: `linear-gradient(90deg, transparent, rgba(212,175,55,${dividerWidth * 0.4}), transparent)`,
              width: '60%',
              margin: '0 auto 50px',
            }}
          />

          {/* Score comparison */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 80,
            }}
          >
            {/* Spotify score */}
            <CountUp
              from={0}
              to={SPOTIFY_DANCEABILITY}
              startFrame={70}
              durationFrames={60}
              color="rgba(255,255,255,0.85)"
              label="Spotify Danceability"
              fps={fps}
            />

            {/* VS separator */}
            <div style={{ opacity: vsOpacity, textAlign: 'center' }}>
              <div
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'rgba(255,255,255,0.25)',
                  letterSpacing: '5px',
                  textTransform: 'uppercase',
                }}
              >
                vs
              </div>
            </div>

            {/* Our score */}
            <CountUp
              from={0}
              to={OUR_DANCEABILITY}
              startFrame={100}
              durationFrames={60}
              color={GOLD}
              label="Music DNA Score"
              fps={fps}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
