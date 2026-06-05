async function loadUser(url) {
  const res = fetch(url);
  return res.json();
}
