import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const GOLD = '#D4AF37';

interface MetricBarProps {
  label: string;
  value: number;
  maxValue: number;
  color: string;
  delayFrames: number;
  fps: number;
  showValue?: boolean;
}

const MetricBar: React.FC<MetricBarProps> = ({
  label,
  value,
  maxValue,
  color,
  delayFrames,
  fps,
  showValue = true,
}) => {
  const frame = useCurrentFrame();
  const progress = spring({
    fps,
    frame: Math.max(0, frame - delayFrames),
    config: { damping: 30, stiffness: 60 },
    durationInFrames: 50,
  });
  const barWidth = interpolate(progress, [0, 1], [0, (value / maxValue) * 100]);
  const opacity = interpolate(
    frame,
    [delayFrames, delayFrames + 15],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <div style={{ opacity, marginBottom: 24 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <span
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 12,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.5)',
            letterSpacing: '2px',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </span>
        {showValue && (
          <span
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 14,
              fontWeight: 700,
              color,
            }}
          >
            {value.toFixed(2)}
          </span>
        )}
      </div>
      <div
        style={{
          height: 6,
          backgroundColor: 'rgba(255,255,255,0.08)',
          borderRadius: 3,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${barWidth}%`,
            backgroundColor: color,
            borderRadius: 3,
            boxShadow: `0 0 12px ${color}60`,
          }}
        />
      </div>
    </div>
  );
};

export const Scene3SplitScreen: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const enterProgress = spring({ fps, frame, config: { damping: 40, stiffness: 60 }, durationInFrames: 35 });

  const leftX = interpolate(enterProgress, [0, 1], [-200, 0]);
  const rightX = interpolate(enterProgress, [0, 1], [200, 0]);

  const dividerOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' });

  const deltaOpacity = interpolate(frame, [80, 100], [0, 1], { extrapolateRight: 'clamp' });
  const deltaY = interpolate(frame, [80, 100], [20, 0], { extrapolateRight: 'clamp' });

  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{ backgroundColor: '#0a0a0a', opacity: exitOpacity, overflow: 'hidden' }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
        }}
      >
        {/* Left panel — Algorithmic / Spotify */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: '60px 70px',
            transform: `translateX(${leftX}px)`,
            borderRight: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 11,
              fontWeight: 600,
              color: 'rgba(255,255,255,0.25)',
              letterSpacing: '5px',
              textTransform: 'uppercase',
              marginBottom: 12,
            }}
          >
            Algorithmic View
          </div>
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 32,
              fontWeight: 700,
              color: 'rgba(255,255,255,0.7)',
              letterSpacing: '-0.5px',
              marginBottom: 40,
            }}
          >
            Generic Metrics
          </div>

          <MetricBar label="Danceability" value={0.41} maxValue={1} color="rgba(255,255,255,0.6)" delayFrames={20} fps={fps} />
          <MetricBar label="Energy" value={0.68} maxValue={1} color="rgba(255,255,255,0.6)" delayFrames={35} fps={fps} />
          <MetricBar label="Valence" value={0.52} maxValue={1} color="rgba(255,255,255,0.6)" delayFrames={50} fps={fps} />

          <div
            style={{
              marginTop: 40,
              padding: '16px 20px',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 8,
              opacity: deltaOpacity,
              transform: `translateY(${deltaY}px)`,
            }}
          >
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 11,
                color: 'rgba(255,255,255,0.3)',
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              Classifier Output
            </div>
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 20,
                fontWeight: 600,
                color: 'rgba(255,255,255,0.5)',
              }}
            >
              "Afrobeats" — confidence 94%
            </div>
          </div>
        </div>

        {/* Right panel — Diaspora Engine */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: '60px 70px',
            transform: `translateX(${rightX}px)`,
          }}
        >
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 11,
              fontWeight: 600,
              color: `${GOLD}80`,
              letterSpacing: '5px',
              textTransform: 'uppercase',
              marginBottom: 12,
            }}
          >
            Diaspora Engine
          </div>
          <div
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: 32,
              fontWeight: 700,
              color: GOLD,
              letterSpacing: '-0.5px',
              marginBottom: 40,
            }}
          >
            Music DNA Metrics
          </div>

          <MetricBar label="Danceability" value={0.745} maxValue={1} color={GOLD} delayFrames={20} fps={fps} />
          <MetricBar label="Syncopation" value={0.445} maxValue={1} color={GOLD} delayFrames={35} fps={fps} />
          <MetricBar label="Log Drum Score" value={1.0} maxValue={1} color={GOLD} delayFrames={50} fps={fps} />

          <div
            style={{
              marginTop: 40,
              padding: '16px 20px',
              border: `1px solid ${GOLD}30`,
              borderRadius: 8,
              background: `${GOLD}08`,
              opacity: deltaOpacity,
              transform: `translateY(${deltaY}px)`,
            }}
          >
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 11,
                color: `${GOLD}70`,
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              True Classification
            </div>
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 20,
                fontWeight: 600,
                color: GOLD,
              }}
            >
              Amapiano — Log Drum Confirmed
            </div>
          </div>
        </div>
      </div>

      {/* Delta callout */}
      <div
        style={{
          position: 'absolute',
          top: 50,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: dividerOpacity,
        }}
      >
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 13,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.2)',
            letterSpacing: '4px',
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          Tshwala Bam · Metric Delta
        </div>
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 20,
            fontWeight: 700,
            color: GOLD,
          }}
        >
          +0.33 Danceability Delta · Log Drum: 1.0
        </div>
      </div>
    </AbsoluteFill>
  );
};
