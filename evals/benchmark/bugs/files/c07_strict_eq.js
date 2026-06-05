function grant(user) {
  if (user.isAdmin === true) {
    return 'granted';
  }
  return 'denied';
}
