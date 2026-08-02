import React, { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function ParticleField() {
  const ref = useRef()
  const count = 1500
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count * 3; i++) {
      pos[i] = (Math.random() - 0.5) * 100
    }
    return pos
  }, [])

  useFrame((_, delta) => {
    ref.current.rotation.x += delta * 0.005
    ref.current.rotation.y += delta * 0.01
  })

  return (
    <points ref={ref}>
      <bufferGeometry attach="geometry">
        <bufferAttribute attachObject={['attributes', 'position']} array={positions} count={count} itemSize={3} />
      </bufferGeometry>
      <PointMaterial
        attach="material"
        size={0.3}
        color="#8b5cf6"
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

export default function Background3D() {
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: -1 }}>
      <Canvas camera={{ position: [0, 0, 30] }}>
        <ParticleField />
      </Canvas>
    </div>
  )
}