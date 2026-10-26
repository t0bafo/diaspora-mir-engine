import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type { Track } from '../types';

const GOLD = '#D4AF37';

interface ConstellationProps {
  tracks: Track[];
}

export const Scene4Constellation: React.FC<ConstellationProps> = ({ tracks }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  // Axis padding
  const PAD_L = 100;
  const PAD_R = 60;
  const PAD_T = 80;
  const PAD_B = 80;
  const plotW = width - PAD_L - PAD_R;
  const plotH = height - PAD_T - PAD_B;

  // Domain
  const X_MIN = 0.15, X_MAX = 0.65;
  const Y_MIN = -0.05, Y_MAX = 1.1;

  const toScreen = (sx: number, sy: number) => ({
    x: PAD_L + ((sx - X_MIN) / (X_MAX - X_MIN)) * plotW,
    y: PAD_T + (1 - (sy - Y_MIN) / (Y_MAX - Y_MIN)) * plotH,
  });

  // Compute dot data once
  const dots = useMemo(() => {
    return tracks.map((t) => {
      const base = toScreen(t.syncopation, t.log_drum);
      const isAmapiano = t.genre === 'amapiano' || t.genre === 'afropiano';
      // Amapiano breaks upward; afrobeats stays put
      const floatY = isAmapiano ? -40 : 0;
      return { ...base, floatY, isAmapiano, genre: t.genre };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tracks]);

  // Break-away happens mid-scene (~frame 200 local)
  const breakFrame = 200;
  const breakProgress = spring({
    fps,
    frame: Math.max(0, frame - breakFrame),
    config: { damping: 25, stiffness: 35 },
    durationInFrames: 120,
  });

  const axisOpacity = interpolate(frame, [30, 60], [0, 1], { extrapolateRight: 'clamp' });
  const labelOpacity = interpolate(frame, [60, 90], [0, 1], { extrapolateRight: 'clamp' });
  const textOpacity = interpolate(frame, [breakFrame + 60, breakFrame + 90], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Axis ticks
  const xTicks = [0.2, 0.3, 0.4, 0.5, 0.6];
  const yTicks = [0, 0.25, 0.5, 0.75, 1.0];

  return (
    <AbsoluteFill style={{ backgroundColor: '#0a0a0a', opacity: exitOpacity }}>
      {/* Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }}
      />

      <svg width={width} height={height} style={{ position: 'absolute', inset: 0 }}>
        {/* Axis lines */}
        <g opacity={axisOpacity}>
          {/* X axis */}
          <line
            x1={PAD_L}
            y1={PAD_T + plotH}
            x2={PAD_L + plotW}
            y2={PAD_T + plotH}
            stroke="rgba(255,255,255,0.15)"
            strokeWidth={1}
          />
          {/* Y axis */}
          <line
            x1={PAD_L}
            y1={PAD_T}
            x2={PAD_L}
            y2={PAD_T + plotH}
            stroke="rgba(255,255,255,0.15)"
            strokeWidth={1}
          />

          {/* X ticks */}
          {xTicks.map((v) => {
            const sx = PAD_L + ((v - X_MIN) / (X_MAX - X_MIN)) * plotW;
            return (
              <g key={v}>
                <line
                  x1={sx}
                  y1={PAD_T + plotH}
                  x2={sx}
                  y2={PAD_T + plotH + 6}
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth={1}
                />
                <text
                  x={sx}
                  y={PAD_T + plotH + 22}
                  fill="rgba(255,255,255,0.3)"
                  fontSize={11}
                  textAnchor="middle"
                  fontFamily="Inter, sans-serif"
                >
                  {v.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Y ticks */}
          {yTicks.map((v) => {
            const sy = PAD_T + (1 - (v - Y_MIN) / (Y_MAX - Y_MIN)) * plotH;
            return (
              <g key={v}>
                <line
                  x1={PAD_L - 6}
                  y1={sy}
                  x2={PAD_L}
                  y2={sy}
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth={1}
                />
                <text
                  x={PAD_L - 14}
                  y={sy + 4}
                  fill="rgba(255,255,255,0.3)"
                  fontSize={11}
                  textAnchor="end"
                  fontFamily="Inter, sans-serif"
                >
                  {v.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Axis labels */}
          <text
            x={PAD_L + plotW / 2}
            y={height - 20}
            fill="rgba(255,255,255,0.4)"
            fontSize={12}
            textAnchor="middle"
            fontFamily="Inter, sans-serif"
            letterSpacing="3"
          >
            SYNCOPATION →
          </text>
          <text
            x={22}
            y={PAD_T + plotH / 2}
            fill="rgba(255,255,255,0.4)"
            fontSize={12}
            textAnchor="middle"
            fontFamily="Inter, sans-serif"
            letterSpacing="3"
            transform={`rotate(-90, 22, ${PAD_T + plotH / 2})`}
          >
            LOG DRUM →
          </text>
        </g>

        {/* Dots */}
        {dots.map((dot, i) => {
          const dotEnter = spring({
            fps,
            frame: Math.max(0, frame - Math.floor(i * 0.3)),
            config: { damping: 30, stiffness: 80 },
            durationInFrames: 25,
          });

          const floatOffset = dot.isAmapiano
            ? interpolate(breakProgress, [0, 1], [0, dot.floatY])
            : 0;

          const dotOpacity = interpolate(dotEnter, [0, 1], [0, dot.isAmapiano ? 0.85 : 0.5]);
          const r = dot.isAmapiano ? 5 : 3.5;
          const color = dot.isAmapiano ? GOLD : 'rgba(255,255,255,0.7)';
          const glowOpacity = dot.isAmapiano ? 0.25 : 0;

          return (
            <g key={i} transform={`translate(${dot.x}, ${dot.y + floatOffset})`}>
              {/* Glow */}
              <circle r={r + 6} fill={GOLD} opacity={glowOpacity * dotOpacity} />
              <circle r={r} fill={color} opacity={dotOpacity} />
            </g>
          );
        })}

        {/* Legend */}
        <g opacity={labelOpacity}>
          <circle cx={PAD_L + plotW - 140} cy={PAD_T + 30} r={5} fill={GOLD} opacity={0.85} />
          <text
            x={PAD_L + plotW - 128}
            y={PAD_T + 35}
            fill={GOLD}
            fontSize={13}
            fontFamily="Inter, sans-serif"
            fontWeight="600"
          >
            Amapiano
          </text>
          <circle cx={PAD_L + plotW - 140} cy={PAD_T + 55} r={3.5} fill="rgba(255,255,255,0.7)" />
          <text
            x={PAD_L + plotW - 128}
            y={PAD_T + 59}
            fill="rgba(255,255,255,0.5)"
            fontSize={13}
            fontFamily="Inter, sans-serif"
          >
            Afrobeats
          </text>
        </g>
      </svg>

      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 30,
          left: PAD_L,
          opacity: axisOpacity,
        }}
      >
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 11,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.3)',
            letterSpacing: '4px',
            textTransform: 'uppercase',
            marginBottom: 6,
          }}
        >
          294 Tracks · Genre Constellation
        </div>
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 24,
            fontWeight: 700,
            color: '#ffffff',
            letterSpacing: '-0.5px',
          }}
        >
          Syncopation vs Log Drum Presence
        </div>
      </div>

      {/* Break-away caption */}
      <div
        style={{
          position: 'absolute',
          bottom: 50,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: textOpacity,
          padding: '0 80px',
        }}
      >
        <div
          style={{
            fontFamily: 'Inter, sans-serif',
            fontSize: 22,
            fontWeight: 600,
            color: '#ffffff',
            letterSpacing: '-0.3px',
            lineHeight: 1.5,
          }}
        >
          The algorithm sees one genre.{' '}
          <span style={{ color: GOLD }}>The math sees two worlds.</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
