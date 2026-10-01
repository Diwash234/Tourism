import { useState, useEffect } from 'react'

// TEST 7a: state box named *Ref, mutated in effect, read during render
export function T7a() {
  const [renderCountRef] = useState(() => ({ current: 0 }))
  useEffect(() => { renderCountRef.current += 1 })
  return <div>{renderCountRef.current}</div>
}

// TEST 7b: same with explicit assignment
export function T7b() {
  const [countRef] = useState(() => ({ current: 0 }))
  useEffect(() => { countRef.current = countRef.current + 1 })
  return <div>{countRef.current}</div>
}
