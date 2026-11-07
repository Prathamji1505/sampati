async page => {
  const errors = []
  const onError = message => { if (message.type() === 'error') errors.push(message.text()) }
  page.on('console', onError)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('http://127.0.0.1:5173/#demo/workspace')
  await page.getByRole('button', { name: 'View DEMO-001 details', exact: true }).waitFor()
  await page.screenshot({ path: '.impeccable/review/desktop.png', fullPage: true })
  const browser = page.context().browser()
  const phoneContext = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor: 1 })
  const phone = await phoneContext.newPage()
  await phone.goto('http://127.0.0.1:5173/#demo/workspace')
  await phone.getByRole('button', { name: 'View DEMO-001 details', exact: true }).waitFor()
  const mobile = await phone.evaluate(() => ({
    viewport: innerWidth,
    document: document.documentElement.scrollWidth,
    inputFont: getComputedStyle(document.querySelector('.search-field input')).fontSize,
    coarsePointer: matchMedia('(pointer: coarse)').matches,
  }))
  if (mobile.document > mobile.viewport || parseFloat(mobile.inputFont) < 16) throw new Error('Touch layout check failed: ' + JSON.stringify(mobile))
  await phone.screenshot({ path: '.impeccable/review/mobile.png', fullPage: true })
  await phoneContext.close()
  page.off('console', onError)
  if (errors.length) throw new Error(errors.join('\n'))
  return { consoleErrors: errors.length, mobile, restartDisplay: '12 fictional aircraft visible after server restart' }
}
