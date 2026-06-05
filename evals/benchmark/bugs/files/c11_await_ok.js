async function loadUser(url) {
  const res = await fetch(url);
  return res.json();
}
