import React from 'react'
import { LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

/**
 * StrategyChart Component
 * 
 * Displays:
 * 1. Dynamic line chart of threat index history
 * 2. Radar chart of current pillar weights (Nash Equilibrium strategy)
 * 3. Game theory adaptation metrics
 */
function StrategyChart({ weights, threatHistory, strategyMetrics }) {
  // Prepare threat history data for chart
  const threatData = threatHistory.map((value, index) => ({
    chunk: index + 1,
    threat: (value * 100).toFixed(1),
  }))

  // Prepare radar data for pillar weights
  const radarData = [
    {
      name: 'Linguistic',
      current: (weights[0] * 100).toFixed(1),
      optimal: 33.3,
    },
    {
      name: 'Behavioral',
      current: (weights[1] * 100).toFixed(1),
      optimal: 33.3,
    },
    {
      name: 'Acoustic',
      current: (weights[2] * 100).toFixed(1),
      optimal: 33.3,
    },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Threat Timeline Chart */}
      <div className="cyber-card">
        <h3 className="font-mono font-bold text-sm text-cyber-cyan mb-4">Threat Index Timeline</h3>

        {threatHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={threatData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 217, 255, 0.1)" />
              <XAxis
                dataKey="chunk"
                stroke="rgba(200, 200, 200, 0.5)"
                style={{ fontSize: '12px', fontFamily: 'monospace' }}
              />
              <YAxis
                stroke="rgba(200, 200, 200, 0.5)"
                domain={[0, 100]}
                style={{ fontSize: '12px', fontFamily: 'monospace' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(10, 14, 39, 0.9)',
                  border: '1px solid rgba(0, 217, 255, 0.3)',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                }}
                labelStyle={{ color: '#00d9ff' }}
                formatter={(value) => [`${value}%`, 'Threat']}
              />

              {/* Threat line with color zones */}
              <Line
                type="monotone"
                dataKey="threat"
                stroke="url(#threatGradient)"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />

              {/* Threshold lines */}
              <line
                x1="0"
                y1="55%"
                x2="100%"
                y2="55%"
                stroke="rgba(255, 0, 85, 0.2)"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-500 font-mono text-sm">
            No threat data yet
          </div>
        )}

        {/* Threshold indicator */}
        <div className="flex justify-between mt-4 text-xs font-mono text-gray-400">
          <span>0%</span>
          <span className="text-cyber-red">55% Verification Threshold</span>
          <span>100%</span>
        </div>
      </div>

      {/* Strategy Weights Radar */}
      <div className="cyber-card">
        <h3 className="font-mono font-bold text-sm text-cyber-cyan mb-4">Pillar Weight Distribution</h3>

        <ResponsiveContainer width="100%" height={250}>
          <RadarChart data={radarData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <PolarGrid stroke="rgba(0, 217, 255, 0.1)" />
            <PolarAngleAxis
              dataKey="name"
              stroke="rgba(200, 200, 200, 0.6)"
              style={{ fontSize: '11px', fontFamily: 'monospace' }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              stroke="rgba(200, 200, 200, 0.3)"
              style={{ fontSize: '10px', fontFamily: 'monospace' }}
            />

            <Radar
              name="Current Weights"
              dataKey="current"
              stroke="#0066ff"
              fill="#0066ff"
              fillOpacity={0.3}
              isAnimationActive={false}
            />
            <Radar
              name="Baseline (33%)"
              dataKey="optimal"
              stroke="rgba(200, 200, 200, 0.4)"
              fill="none"
              strokeDasharray="5 5"
              isAnimationActive={false}
            />

            <Legend
              wrapperStyle={{ fontFamily: 'monospace', fontSize: '12px', paddingTop: '20px' }}
              textColor="rgba(200, 200, 200, 0.8)"
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Strategy Metrics */}
      <div className="lg:col-span-2 cyber-card">
        <h3 className="font-mono font-bold text-sm text-cyber-cyan mb-4">Game Theory Metrics</h3>

        {strategyMetrics ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Game Round</p>
              <p className="text-lg font-mono font-bold text-cyber-cyan">
                {strategyMetrics.round || 0}
              </p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Strategy Entropy</p>
              <p className="text-lg font-mono font-bold text-cyber-blue">
                {(strategyMetrics.strategy_entropy || 0).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 font-mono mt-1">(0=Pure, 1.58=Mixed)</p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Linguistic Weight</p>
              <p className="text-lg font-mono font-bold text-cyber-cyan">
                {((strategyMetrics.defender_strategy?.[0] || 0) * 100).toFixed(0)}%
              </p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Behavioral Weight</p>
              <p className="text-lg font-mono font-bold text-cyber-blue">
                {((strategyMetrics.defender_strategy?.[1] || 0) * 100).toFixed(0)}%
              </p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Acoustic Weight</p>
              <p className="text-lg font-mono font-bold text-cyber-purple">
                {((strategyMetrics.defender_strategy?.[2] || 0) * 100).toFixed(0)}%
              </p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Last Threat Index</p>
              <p className="text-lg font-mono font-bold text-cyber-red">
                {(strategyMetrics.threat_history?.[strategyMetrics.threat_history?.length - 1] || 0).toFixed(2)}
              </p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Threat Count (>0.55)</p>
              <p className="text-lg font-mono font-bold text-cyber-red">
                {strategyMetrics.threat_history?.filter((t) => t > 0.55).length || 0}
              </p>
            </div>

            <div className="bg-cyber-darker rounded p-3">
              <p className="text-xs text-gray-400 font-mono mb-1">Max Threat</p>
              <p className="text-lg font-mono font-bold text-cyber-red">
                {Math.max(...(strategyMetrics.threat_history || [0])).toFixed(2)}
              </p>
            </div>
          </div>
        ) : (
          <div className="text-gray-500 font-mono text-sm">No strategy data available</div>
        )}
      </div>
    </div>
  )
}

export default StrategyChart
