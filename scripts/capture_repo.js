// Run through playwright-cli run-code --filename=scripts/capture_repo.js.
// Captures the fictional demo only; it never confirms the generated preview.
async page => {
  const origin = 'http://127.0.0.1:5173/';
  const errors = [];
  const onError = message => { if (message.type() === 'error') errors.push(message.text()); };
  page.on('console', onError);
  const beforeResponse = await page.request.get(origin + 'api/demo/workspace');
  if (!beforeResponse.ok()) throw new Error('The local demo API is not ready.');
  const before = await beforeResponse.json();
  if (!before.aircraft.length) throw new Error('Populate the fictional demo before capturing the register.');
  const settle = async () => page.evaluate(async () => {
    await document.fonts.ready;
    document.activeElement?.blur();
    scrollTo(0, 0);
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(origin);
  await page.getByRole('heading', { name: 'Sampati', exact: true }).waitFor();
  await settle();
  if (!await page.evaluate(() => document.fonts.check('25px "Yatra One"'))) {
    throw new Error('The public display font failed to load.');
  }
  await page.screenshot({ path: 'docs/images/welcome.png' });

  const widths = [];
  for (const width of [1440, 1024, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await settle();
    const content = await page.evaluate(() => document.documentElement.scrollWidth);
    if (content > width) throw new Error('Welcome overflow at ' + width);
    widths.push({ width, content });
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(origin + '#demo/workspace');
  await page.getByRole('heading', { name: 'Aircraft register', exact: true }).waitFor();
  await page.getByRole('button', { name: 'View DEMO-001 details', exact: true }).waitFor();
  await settle();
  await page.screenshot({ path: 'docs/images/register.png' });

  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: 'Import dataset', exact: true }).click();
  await page.getByRole('button', { name: 'Use sample', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm import', exact: true }).waitFor();
  await settle();
  await page.screenshot({ path: 'docs/images/import-preview.png' });

  await page.getByRole('button', { name: 'Import history', exact: true }).click();
  await page.getByRole('heading', { name: 'Import history', exact: true }).waitFor();
  await settle();
  await page.screenshot({ path: 'docs/images/history.png' });

  const phoneContext = await page.context().browser().newContext({
    viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true,
    deviceScaleFactor: 1,
  });
  try {
    const phone = await phoneContext.newPage();
    phone.on('console', onError);
    await phone.goto(origin + '#demo/workspace');
    await phone.getByRole('button', { name: 'View DEMO-001 details', exact: true }).waitFor();
    await phone.evaluate(async () => { await document.fonts.ready; document.activeElement?.blur(); scrollTo(0, 0); });
    const layout = await phone.evaluate(() => ({
      width: innerWidth, content: document.documentElement.scrollWidth,
      inputSize: getComputedStyle(document.querySelector('.search-field input')).fontSize,
    }));
    if (layout.content > layout.width || parseFloat(layout.inputSize) < 16) {
      throw new Error('Mobile layout regressed: ' + JSON.stringify(layout));
    }
    await phone.screenshot({ path: 'docs/images/mobile.png' });
  } finally {
    await phoneContext.close();
  }
  const after = await (await page.request.get(origin + 'api/demo/workspace')).json();
  if (after.revision !== before.revision || after.imports.length !== before.imports.length) {
    throw new Error('Screenshot capture changed accepted demo data.');
  }
  page.off('console', onError);
  if (errors.length) throw new Error(errors.join('\n'));
  return { screenshots: 5, widths, consoleErrors: errors.length, revision: after.revision, acceptedRecordsUnchanged: true };
}
