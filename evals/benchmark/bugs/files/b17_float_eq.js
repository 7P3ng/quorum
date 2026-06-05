function isFullPrice(total) {
  return total === 0.1 + 0.2;   // 0.1+0.2 !== 0.3 in IEEE754
}
