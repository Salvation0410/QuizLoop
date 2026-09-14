export function answersMatch (correct: string[], selected: string[]): boolean {
  if (selected.length !== new Set(selected).size || selected.length !== correct.length) return false
  const expected = new Set(correct)
  return selected.every(answer => expected.has(answer))
}
