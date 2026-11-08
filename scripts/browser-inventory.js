async page => {
  const check=(ok,message)=>{if(!ok)throw new Error(message)}
  const origin='http://127.0.0.1:5173';const suffix=crypto.randomUUID().replaceAll('-','').slice(0,14)
  const generated=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('sampati-inventory-qa-ids')||'[]'))
  const errors=[];let expectedConflict=false
  page.on('console',message=>{if(message.type()==='error' && !(expectedConflict && message.location().url.endsWith('/api/inventory/records') && message.text().includes('409')))errors.push(message.text())})
  page.on('pageerror',error=>errors.push(error.message))
  const get=async(target,path)=>(await target.request.get(origin+'/api'+path)).json()
  const post=(target,path,body,csrf)=>target.request.post(origin+'/api'+path,{headers:{'X-Sampati-Request':'1','X-CSRF-Token':csrf},data:body})
  async function signup(target,index){
    await target.goto(origin+'/#register')
    await target.getByLabel('Your name',{exact:true}).fill('Browser QA inventory '+index)
    await target.getByLabel('Organisation name',{exact:true}).fill('Browser QA organisation inventory '+suffix+index)
    await target.getByLabel('Username',{exact:true}).fill('qa-browser-'+suffix+index)
    await target.getByLabel('Password',{exact:true}).fill('Fictional QA '+crypto.randomUUID())
    await target.getByRole('button',{name:'Create account & workspace',exact:true}).click()
    await target.getByRole('heading',{name:'Aircraft register',exact:true}).waitFor()
    const auth=await get(target,'/auth/session');generated.push(auth.user.id)
    await page.evaluate(ids=>sessionStorage.setItem('sampati-inventory-qa-ids',JSON.stringify(ids)),generated)
    return auth
  }
  async function navigate(target,name){const toggle=target.getByRole('button',{name:'Toggle navigation',exact:true});if(await toggle.isVisible())await toggle.click();await target.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name,exact:true}).click()}
  async function capture(kind){for(const width of [1440,1024,390,320]){await page.setViewportSize({width,height:1000});await page.evaluate(async()=>{await document.fonts.ready;document.activeElement?.blur();scrollTo(0,0);await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),kind+' overflow '+width);await page.screenshot({path:'.impeccable/review/inventory-'+kind+'-'+width+'.png',fullPage:true})}await page.setViewportSize({width:1440,height:1000})}
  async function fillEvent(target,reference,quantity){await target.getByRole('textbox',{name:'Event reference',exact:true}).fill(reference);await target.getByRole('spinbutton',{name:'Quantity (packs)',exact:true}).fill(quantity);await target.getByRole('textbox',{name:'Source or receipt name',exact:true}).fill('Fictional signed store log');await target.getByRole('textbox',{name:'Reason / evidence note',exact:true}).fill('Fictional recorded stock event; no delivery is implied.')}
  async function save(){await page.getByRole('button',{name:'Record stock event',exact:true}).click();await page.getByRole('status').filter({hasText:'Stock event recorded.'}).waitFor()}
  await page.context().clearCookies();await page.setViewportSize({width:1440,height:1000});await page.goto(origin+'/#demo/inventory')
  await page.getByRole('button',{name:'Open DEMO-SHELTER at DEMO-STORE',exact:true}).click()
  await page.getByRole('heading',{name:'Stock history',exact:true}).waitFor()
  check(await page.getByRole('heading',{name:'Record a stock event',exact:true}).count()===0,'Demo mutation form exposed')
  await page.getByText('Against original record: DEMO-STOCK-005',{exact:true}).waitFor()
  const auth=await signup(page,1)
  await navigate(page,'Relief requests');await page.getByRole('button',{name:'New request',exact:true}).click();await page.getByRole('button',{name:'Use fictional example',exact:true}).click()
  await page.getByLabel('Request reference',{exact:true}).fill('QA-RELIEF-STOCK');await page.getByLabel('Quantity',{exact:true}).fill('40')
  await page.getByRole('button',{name:'Save draft',exact:true}).click();await page.getByRole('heading',{name:'Request history',exact:true}).waitFor()
  for(const status of ['submitted','reviewed']){await page.getByRole('combobox',{name:'Next status',exact:true}).selectOption(status);await page.getByLabel('Reason for status change',{exact:true}).fill('Fictional local need confirmed for stock walkthrough.');await page.getByRole('button',{name:'Update status',exact:true}).click();await page.getByRole('status').filter({hasText:'Status updated to'}).waitFor()}
  const request=(await get(page,'/relief-requests')).items[0]
  await navigate(page,'Aid inventory');await page.getByRole('heading',{name:'Your aid inventory starts here.',exact:true}).waitFor()
  await page.getByRole('button',{name:'Items and locations',exact:true}).click()
  await page.getByLabel('Item code',{exact:true}).fill('QA-WATER');await page.getByLabel('Item name',{exact:true}).fill('Fictional water packs')
  await page.getByRole('button',{name:'Save supply item',exact:true}).click();await page.getByRole('status').filter({hasText:'Supply item saved'}).waitFor()
  await page.getByLabel('Location code',{exact:true}).fill('QA-STORE-A');await page.getByLabel('Location name',{exact:true}).fill('Fictional Riverside store');await page.getByLabel('Storage locality',{exact:true}).fill('Fictional Riverside Ward')
  await page.getByRole('button',{name:'Save storage location',exact:true}).click();await page.getByRole('status').filter({hasText:'Storage location saved'}).waitFor()
  await capture('catalog')
  const catalog=await get(page,'/inventory/catalog');const item=catalog.items[0];const location=catalog.locations[0]
  const positionPath='/inventory/position?'+new URLSearchParams({item_id:item.id,location_id:location.id})
  await page.getByRole('button',{name:'Back to stock register',exact:true}).click();await page.getByRole('button',{name:'Record stock',exact:true}).click();await page.getByRole('button',{name:'Open stock position',exact:true}).click()
  await page.getByRole('heading',{name:'Record a stock event',exact:true}).waitFor();await fillEvent(page,'QA-RECEIPT-001','100.125');await capture('entry');await save()
  await page.getByRole('combobox',{name:'Event type',exact:true}).selectOption('report');await fillEvent(page,'QA-COUNT-001','0');await save()
  let current=await get(page,positionPath);check(current.position.on_hand==='100.125' && current.position.latest_report.quantity==='0','Count report changed usable stock')
  await page.getByRole('combobox',{name:'Event type',exact:true}).selectOption('reserve')
  await page.getByRole('combobox',{name:'Reviewed relief request',exact:true}).selectOption(request.id)
  await fillEvent(page,'QA-RESERVE-001','30.125');await save()
  current=await get(page,positionPath);const reserve=current.records.find(record=>record.kind==='reserve')
  await page.getByRole('combobox',{name:'Event type',exact:true}).selectOption('issue');await page.getByRole('combobox',{name:'Original reservation',exact:true}).selectOption(reserve.id);await fillEvent(page,'QA-ISSUE-001','20.125');await save()
  current=await get(page,positionPath);const issue=current.records.find(record=>record.kind==='issue')
  await page.getByRole('combobox',{name:'Event type',exact:true}).selectOption('release');await page.getByRole('combobox',{name:'Original reservation',exact:true}).selectOption(reserve.id);await fillEvent(page,'QA-RELEASE-001','10');await save()
  await page.getByRole('combobox',{name:'Event type',exact:true}).selectOption('return');await page.getByRole('combobox',{name:'Original issue',exact:true}).selectOption(issue.id);await fillEvent(page,'QA-RETURN-001','5.125');await save()
  current=await get(page,positionPath);check(current.position.on_hand==='85.125' && current.position.reserved==='0' && current.position.available==='85.125','Incorrect fractional lifecycle balances')
  check(current.records.length===6 && current.records[0].parent_reference==='QA-ISSUE-001','History or original issue reference missing')
  await capture('detail')
  const raw={item_id:item.id,location_id:location.id,kind:'receipt',quantity:'1',expected_version:current.position.version,source_name:'Fictional QA store log',observed_at:new Date().toISOString(),reason:'Fictional competing receipt.'}
  check((await post(page,'/inventory/records',{...raw,reference:'QA-COMPETING-001',submission_key:crypto.randomUUID()},auth.csrf_token)).status()===201,'Background stock mutation failed')
  await fillEvent(page,'QA-STALE-001','1');expectedConflict=true;await page.getByRole('button',{name:'Record stock event',exact:true}).click();await page.getByRole('alert').filter({hasText:'This stock position changed after you opened it'}).waitFor()
  check((await get(page,positionPath)).position.on_hand==='86.125','Stale event overwrote stock')
  await page.getByRole('button',{name:'Refresh stock details',exact:true}).click();await page.getByRole('heading',{name:'Stock history',exact:true}).waitFor();expectedConflict=false
  for(let index=1;index<=21;index++){const target=(await(await post(page,'/inventory/locations',{code:'QA-BULK-'+index,name:'Fictional bulk store '+index,locality:'Fictional Hill'},auth.csrf_token)).json()).entry;check((await post(page,'/inventory/records',{...raw,location_id:target.id,expected_version:0,reference:'QA-BULK-RECEIPT-'+index,submission_key:crypto.randomUUID()},auth.csrf_token)).status()===201,'Bulk stock fixture failed')}
  await page.getByRole('button',{name:'Back to stock register',exact:true}).click();await page.getByText('Page 1 of 2',{exact:true}).waitFor();await page.getByRole('button',{name:'Next stock',exact:true}).click();await page.getByText('Page 2 of 2',{exact:true}).waitFor();check(await page.locator('.inventory-table tbody tr').count()===2,'Incorrect second stock page')
  await page.getByRole('textbox',{name:'Search inventory',exact:true}).fill('QA-STORE-A');await page.waitForFunction(()=>document.querySelectorAll('.inventory-table tbody tr').length===1);await capture('list')
  const context2=await page.context().browser().newContext();const other=await context2.newPage();const outsider=await signup(other,2)
  check((await get(other,'/inventory')).total===0,'Foreign stock list leaked');check((await other.request.get(origin+'/api'+positionPath)).status()===404,'Foreign stock details leaked')
  const invitation=await(await post(page,'/team/invitations',{username:outsider.user.username,role:'viewer'},auth.csrf_token)).json();check((await post(other,'/team/invitations/accept',{token:invitation.token},outsider.csrf_token)).status()===200,'Viewer invitation failed')
  await other.goto(origin+'/#inventory');await other.reload();await other.getByRole('button',{name:'Record stock',exact:true}).waitFor();check(await other.getByRole('button',{name:'Record stock',exact:true}).isDisabled(),'Viewer can record stock')
  await other.getByRole('textbox',{name:'Search inventory',exact:true}).fill('QA-STORE-A');await other.getByRole('button',{name:'Open QA-WATER at QA-STORE-A',exact:true}).click();await other.getByRole('heading',{name:'Stock history',exact:true}).waitFor();check(await other.getByRole('heading',{name:'Record a stock event',exact:true}).count()===0,'Viewer stock mutation form exposed')
  await context2.close()
  const retryContext=await page.context().browser().newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await retryContext.addCookies(await page.context().cookies());const retry=await retryContext.newPage()
  await retry.goto(origin+'/#inventory');await retry.getByRole('textbox',{name:'Search inventory',exact:true}).fill('QA-STORE-A');await retry.getByRole('button',{name:'Open QA-WATER at QA-STORE-A',exact:true}).click();await fillEvent(retry,'QA-RETRY-001','1')
  check(await retry.getByRole('spinbutton',{name:'Quantity (packs)',exact:true}).evaluate(el=>parseFloat(getComputedStyle(el).fontSize)>=16),'Phone quantity text too small');check(await retry.getByRole('button',{name:'Record stock event',exact:true}).evaluate(el=>el.getBoundingClientRect().height>=44),'Touch record action too small')
  let drop=true;await retry.route('**/api/inventory/records',async route=>{if(drop){drop=false;await route.fetch();await route.abort('failed')}else await route.continue()})
  await retry.getByRole('button',{name:'Record stock event',exact:true}).click();await retry.getByRole('alert').filter({hasText:'The local server could not be reached'}).waitFor();await retry.getByRole('button',{name:'Record stock event',exact:true}).click();await retry.getByRole('status').filter({hasText:'This event was already recorded'}).waitFor()
  current=await get(page,positionPath);check(current.position.on_hand==='87.125' && current.records.filter(record=>record.reference==='QA-RETRY-001').length===1,'Lost-response retry duplicated stock')
  await retryContext.close()
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:/^Aircraft register/}).click()
  let releaseRefresh,markHeld
  const gate=new Promise(resolve=>{releaseRefresh=resolve});const held=new Promise(resolve=>{markHeld=resolve})
  const holdRefresh=async route=>{markHeld();await gate;try{await route.continue()}catch{/* Sign-out deliberately aborts this in-flight read. */}}
  await page.route('**/api/workspace',holdRefresh)
  await page.getByRole('button',{name:'Refresh register',exact:true}).click();await held
  await page.getByRole('button',{name:'Sign out',exact:true}).click()
  await page.waitForURL('**/#demo/workspace');releaseRefresh();await page.unroute('**/api/workspace',holdRefresh)
  await page.getByRole('heading',{name:'Aircraft register',exact:true}).waitFor()
  check(errors.length===0,'Unexpected browser errors: '+errors.join('; '))
  return {passed:['read-only demo and parent traceability','reviewed relief request in UI','empty private inventory','catalog creation','exact fractional receipt/reserve/issue/release/return','source report stays separate','append-only source/actor/history','stale-event conflict','20-row paging and search','organisation isolation','viewer UI','phone controls','lost-response retry','sign-out cancels in-flight private refresh','16 contained captures at 1440/1024/390/320','zero unexpected main-page errors'],generated}
}
