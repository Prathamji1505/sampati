// Run through playwright-cli run-code --filename=scripts/capture_showcase.js.
// Uses the compiled local app and shared fictional records; never confirms data.
async page => {
  const origin = 'http://127.0.0.1:8000';
  const check = (value, message) => { if (!value) throw new Error(message); };
  const get = async path => {
    const response = await page.request.get(origin + '/api/demo' + path);
    check(response.ok(), 'Demo endpoint unavailable: ' + path);
    return response.json();
  };
  const paths = ['/workspace', '/relief-requests', '/inventory', '/deliveries', '/automation/inbox', '/incidents'];
  const before = await Promise.all(paths.map(get));
  const errors = [], mutations = [], captures = [];
  const consoleError = message => { if (message.type() === 'error') errors.push(message.text()); };
  const pageError = error => errors.push(error.message);
  const request = request => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method()) && !request.url().endsWith('/imports/preview')) mutations.push(request.url());
  };
  const observe = target => { target.on('console', consoleError); target.on('pageerror', pageError); target.on('request', request); };
  observe(page);
  const capture = async (target, name) => {
    await target.evaluate(async () => {
      await document.fonts.ready;
      document.activeElement?.blur();
      scrollTo(0, 0);
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    const layout = await target.evaluate(() => ({ content: document.documentElement.scrollWidth, width: document.documentElement.clientWidth }));
    check(layout.content <= layout.width, name + ': page overflow');
    await target.screenshot({ path: 'docs/images/' + name + '.png' });
    captures.push(name);
  };
  const visit = async (route, heading) => {
    await page.goto(origin + '/#demo/' + route);
    await page.getByRole('heading', { name: heading, exact: true }).waitFor();
  };
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(origin);
  await page.getByRole('heading', { name: 'Sampati', exact: true }).waitFor();
  await capture(page, 'welcome');
  await page.setViewportSize({ width: 1440, height: 1040 });
  const scenes = [
    ['relief-overview', 'overview', 'Relief work awaiting attention'],
    ['incident-review', 'incidents', 'Incident review'],
    ['relief-requests', 'relief', 'Relief requests'],
    ['aid-inventory', 'inventory', 'Aid inventory'],
    ['delivery-tracking', 'deliveries', 'Delivery tracking'],
    ['automation-inbox', 'automation', 'Automation inbox'],
  ];
  for (const [name, route, title] of scenes) {
    await visit(route, title);
    if (route === 'overview') await page.getByRole('heading', { name: 'Reviewed needs still awaiting delivery', exact: true }).waitFor();
    if (route === 'incidents') await page.getByRole('button', { name: /DEMO/ }).first().waitFor();
    if (route === 'relief') await page.getByRole('button', { name: /DEMO-REL/ }).first().waitFor();
    if (route === 'inventory') await page.locator('.inventory-table tbody tr').first().waitFor();
    if (route === 'deliveries') await page.getByRole('button', { name: 'Open DEMO-SHIP-001 shipment', exact: true }).waitFor();
    if (route === 'automation') await page.getByRole('button', { name: 'Inspect file DEMO-INTAKE-001', exact: true }).waitFor();
    await capture(page, name);
  }
  await page.getByRole('button', { name: 'Inspect file DEMO-INTAKE-001', exact: true }).click();
  await page.getByRole('heading', { name: 'Intake history', exact: true }).waitFor();
  await capture(page, 'intake-evidence');
  await visit('deliveries', 'Delivery tracking');
  await page.getByRole('button', { name: 'Request follow-up', exact: true }).click();
  await page.getByRole('cell', { name: '30 kits', exact: true }).waitFor();
  await capture(page, 'remaining-needs');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await visit('workspace', 'Aircraft register');
  await page.getByRole('button', { name: 'View DEMO-001 details', exact: true }).waitFor();
  await capture(page, 'register');
  await visit('import', 'Import a dataset');
  await page.getByRole('button', { name: 'Use sample', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm import', exact: true }).waitFor();
  await capture(page, 'import-preview');
  await visit('history', 'Import history');
  await page.locator('.history-list, .history-table, table').first().waitFor();
  await capture(page, 'history');
  const phoneContext = await page.context().browser().newContext({
    viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor: 1,
  });
  try {
    const phone = await phoneContext.newPage();
    observe(phone);
    await phone.goto(origin + '/#demo/automation');
    await phone.getByRole('button', { name: 'Inspect file DEMO-INTAKE-001', exact: true }).waitFor();
    await capture(phone, 'relief-mobile');
    await phone.getByRole('button', { name: 'Toggle navigation', exact: true }).click();
    await phone.getByRole('navigation', { name: 'Main navigation' }).waitFor();
    await capture(phone, 'navigation-mobile');
    await phone.goto(origin + '/#demo/workspace');
    await phone.getByRole('button', { name: 'View DEMO-001 details', exact: true }).waitFor();
    await capture(phone, 'mobile');
  } finally { await phoneContext.close(); }
  const after = await Promise.all(paths.map(get));
  check(after[0].revision === before[0].revision && after[0].imports.length === before[0].imports.length, 'Captures changed accepted aircraft data');
  for (let i = 1; i < paths.length; i++) check(after[i].total === before[i].total, 'Captures changed ' + paths[i]);
  check(mutations.length === 0, 'Unexpected write request');
  check(errors.length === 0, errors.join('; '));
  page.off('console', consoleError); page.off('pageerror', pageError); page.off('request', request);
  return { captures, fictionalDemoOnly: true, acceptedDataUnchanged: true, writes: mutations.length, consoleErrors: errors.length };
}
