import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const GOLD = '#D4AF37';

export const Scene5Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Fade in from black
  const bgOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });

  const logoSpring = spring({
    fps,
    frame: Math.max(0, frame - 20),
    config: { damping: 30, stiffness: 50 },
    durationInFrames: 60,
  });

  const titleY = interpolate(logoSpring, [0, 1], [40, 0]);
  const titleOpacity = interpolate(logoSpring, [0, 1], [0, 1]);

  const subtitleOpacity = interpolate(frame, [70, 100], [0, 1], { extrapolateRight: 'clamp' });
  const subtitleY = interpolate(frame, [70, 100], [20, 0], { extrapolateRight: 'clamp' });

  const lineWidth = interpolate(frame, [50, 100], [0, 1], { extrapolateRight: 'clamp' });

  const taglineOpacity = interpolate(frame, [110, 140], [0, 1], { extrapolateRight: 'clamp' });

  const metricOpacity = interpolate(frame, [150, 180], [0, 1], { extrapolateRight: 'clamp' });
  const metricY = interpolate(frame, [150, 180], [15, 0], { extrapolateRight: 'clamp' });

  // Final fade to pure black
  const finalFade = interpolate(
    frame,
    [durationInFrames - 45, durationInFrames - 5],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const stats = [
    { value: '294', label: 'Tracks Analysed' },
    { value: '3', label: 'Genre Classes' },
    { value: '7', label: 'Feature Dimensions' },
    { value: '1.3.0', label: 'Corpus Version' },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: '#0a0a0a' }}>
      {/* Radial glow */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse 60% 50% at 50% 50%, ${GOLD}08 0%, transparent 70%)`,
          opacity: bgOpacity,
        }}
      />

      {/* Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(212,175,55,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(212,175,55,0.025) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          opacity: bgOpacity,
        }}
      />

      {/* Content */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 0,
        }}
      >
        {/* Wordmark */}
        <div
          style={{
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
            textAlign: 'center',
            marginBottom: 20,
          }}
        >
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 96,
              fontWeight: 900,
              color: '#ffffff',
              letterSpacing: '-4px',
              lineHeight: 1,
            }}
          >
            Music
          </div>
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 96,
              fontWeight: 900,
              color: GOLD,
              letterSpacing: '-4px',
              lineHeight: 1,
            }}
          >
            DNA
          </div>
        </div>

        {/* Divider line */}
        <div
          style={{
            width: `${lineWidth * 200}px`,
            height: 1,
            background: `linear-gradient(90deg, transparent, ${GOLD}60, transparent)`,
            marginBottom: 24,
          }}
        />

        {/* Subtitle */}
        <div
          style={{
            opacity: subtitleOpacity,
            transform: `translateY(${subtitleY}px)`,
            fontFamily: 'Inter, sans-serif',
            fontSize: 18,
            fontWeight: 400,
            color: 'rgba(255,255,255,0.55)',
            letterSpacing: '0.5px',
            textAlign: 'center',
            marginBottom: 60,
          }}
        >
          Built for the music the algorithm missed.
        </div>

        {/* Stats row */}
        <div
          style={{
            opacity: metricOpacity,
            transform: `translateY(${metricY}px)`,
            display: 'flex',
            gap: 60,
          }}
        >
          {stats.map(({ value, label }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 32,
                  fontWeight: 800,
                  color: GOLD,
                  letterSpacing: '-1px',
                  lineHeight: 1,
                  marginBottom: 6,
                }}
              >
                {value}
              </div>
              <div
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: 11,
                  fontWeight: 500,
                  color: 'rgba(255,255,255,0.3)',
                  letterSpacing: '3px',
                  textTransform: 'uppercase',
                }}
              >
                {label}
              </div>
            </div>
          ))}
        </div>

        {/* Tagline */}
        <div
          style={{
            position: 'absolute',
            bottom: 50,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: taglineOpacity,
          }}
        >
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 12,
              fontWeight: 500,
              color: 'rgba(255,255,255,0.2)',
              letterSpacing: '5px',
              textTransform: 'uppercase',
            }}
          >
            Corpus v1.3.0 · Essentia Backend · 294 Tracks
          </div>
        </div>
      </div>

      {/* Final fade to black overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: '#000000',
          opacity: finalFade,
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};
