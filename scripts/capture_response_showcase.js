// Capture real response UI with fictional fixtures in a disposable test service.
// Start scripts/showcase_server.py first. Never run against live data.
async page => {
  const origin = 'http://127.0.0.1:5173';
  const check = (value, message) => { if (!value) throw new Error(message); };
  const marker = await (await page.request.get(origin + '/api/showcase-status')).json();
  check(marker.fictional && marker.disposable_test_schema, 'A disposable fictional showcase server is required.');
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  const stamp = Date.now().toString(36); const username = 'response-qa-' + stamp;
  const post = async (path, body, csrf) => {
    const response = await page.request.post(origin + '/api' + path, { headers: {'X-Sampati-Request': '1', ...(csrf ? {'X-CSRF-Token': csrf} : {})}, data: body });
    check(response.ok(), path + ' returned ' + response.status()); return response.json();
  };
  const get = async path => { const response = await page.request.get(origin + '/api' + path); check(response.ok(), path + ' failed'); return response.json(); };
  const localDate = value => new Date(value.getTime() - value.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  const capture = async (name, focus) => {
    await page.evaluate(async () => { await document.fonts.ready; document.activeElement?.blur(); scrollTo(0, 0); });
    const layout = await page.evaluate(() => ({width: innerWidth, content: document.documentElement.scrollWidth}));
    check(layout.content <= layout.width, name + ': page overflows');
    if (focus) await focus.evaluate(el => scrollTo(0, el.getBoundingClientRect().top + scrollY - 85));
    await page.screenshot({path: 'docs/images/' + name + '.png'});
  };
  await page.setViewportSize({width:1440,height:1040});
  await page.goto(origin + '/#demo/response');
  await page.reload();
  await page.getByRole('heading', {name:'No warning reports yet',exact:true}).waitFor();
  check(await page.getByRole('button',{name:'Record unreviewed warning',exact:true}).count() === 0, 'Demo exposed write form');

  const auth = await post('/auth/signup', {username,password:'Fictional ' + crypto.randomUUID(),display_name:'Fictional response reviewer',organisation_name:'Fictional relief coordination team'});
  const csrf = auth.csrf_token;
  const csv = 'aircraft_id,display_name,reported_status,source_updated_at,source_name,note\nQA-CIV-1,Fictional support aircraft,available,' + new Date().toISOString() + ',Fictional fleet log,Fictional QA only\n';
  const previewResponse = await page.request.post(origin+'/api/imports/preview',{headers:{'X-CSRF-Token':csrf},multipart:{file:{name:'fictional-aircraft.csv',mimeType:'text/csv',buffer:Buffer.from(csv)}}});
  check(previewResponse.ok(),'Aircraft preview failed'); const preview=await previewResponse.json();
  await post('/imports/confirm',{token:preview.token,rows:preview.rows},csrf);
  const item=(await post('/inventory/items',{code:'QA-WATER',name:'Fictional water packs',category:'water',unit:'packs'},csrf)).entry;
  const store=(await post('/inventory/locations',{code:'QA-STORE',name:'Fictional river store',locality:'Fictional River Ward'},csrf)).entry;
  const stock={item_id:item.id,location_id:store.id,reference:'QA-RECEIPT',submission_key:crypto.randomUUID(),expected_version:0,kind:'receipt',quantity:'100',source_name:'Fictional signed receipt',observed_at:new Date().toISOString(),reason:'Fictional software check.'};
  await post('/inventory/records',stock,csrf);
  let need=(await post('/relief-requests',{reference:'QA-NEED',submission_key:crypto.randomUUID(),requesting_organisation:'Fictional ward desk',locality:'Fictional River Ward',category:'water',item_name:'Fictional water packs',quantity:'40',unit:'packs',needed_by:new Date(Date.now()+86400000).toISOString(),source_name:'Fictional ward log',note:'Fictional software test only.'},csrf)).request;
  for(const status of ['submitted','reviewed']) need=(await post('/relief-requests/'+need.id+'/status',{status,expected_version:need.version,reason:'Fictional details verified.'},csrf)).request;
  await page.goto(origin + '/#response'); await page.reload();
  await page.getByRole('heading',{name:'No warning reports yet',exact:true}).waitFor();
  await page.getByText('Record a warning or news report',{exact:true}).click();
  const reference = page.getByLabel('Warning reference',{exact:true});
  await reference.fill('QA/WARN-01');
  check(await reference.evaluate(input => input.checkValidity()), 'A slash/hyphen reference failed native validation');
  await reference.fill('QA!WARN');
  check(!await reference.evaluate(input => input.checkValidity()), 'Invalid reference punctuation passed native validation');
  for(const [name,value] of Object.entries({'Warning reference':'QA-WARN','Warning title':'Fictional river warning','Affected locality':'Fictional River Ward','Warning source':'Fictional district desk','Reported warning details':'Fictional warning evidence for testing only.'})) await page.getByLabel(name,{exact:true}).fill(value);
  await page.getByLabel('Reported severity',{exact:true}).selectOption('severe');
  await page.getByLabel('Reported certainty',{exact:true}).selectOption('observed');
  await page.getByLabel('Warning expires at (local time)',{exact:true}).fill(localDate(new Date(Date.now()+4*3600000)));
  await page.getByRole('button',{name:'Record unreviewed warning',exact:true}).click();
  const warning=page.locator('.response-record').filter({hasText:'Fictional river warning'});
  await warning.locator('summary').click();
  await warning.getByLabel('Warning review reason',{exact:true}).fill('Fictional primary evidence checked for preparation.');
  await warning.getByRole('button',{name:'Record warning review',exact:true}).click();
  await warning.locator('.response-good').waitFor();
  await capture('warning-review');
  await warning.getByRole('button',{name:'Prepare this response',exact:true}).click();
  await page.getByLabel('Workflow title',{exact:true}).fill('Fictional river relief preparation');
  await page.getByRole('button',{name:'Add supply need',exact:true}).click();
  await page.getByLabel('Request for need 1',{exact:true}).selectOption(need.id);
  await page.getByLabel('Catalog item for need 1',{exact:true}).selectOption(item.id);
  await page.getByLabel('Store for need 1',{exact:true}).selectOption(store.id);
  await page.getByLabel('Kilograms per unit for need 1',{exact:true}).fill('2');
  await page.getByLabel('Weight source for need 1',{exact:true}).fill('Fictional packing sheet');
  await page.getByLabel('I checked that this item is the exact supply requested.',{exact:true}).check();
  await page.getByLabel('Weather assessment',{exact:true}).selectOption('confirmed');
  await page.getByLabel('Destination access assessment',{exact:true}).selectOption('confirmed');
  await page.getByLabel('Context report source',{exact:true}).fill('Fictional operator context log');
  await page.getByRole('button',{name:'Evaluate response workflow',exact:true}).click();
  await page.getByRole('heading',{name:'Resolve these checks before review',exact:true}).waitFor();
  check(await page.getByText('support missing',{exact:false}).count()>0,'Missing support was not explained');
  await capture('response-blockers', page.locator('.response-result'));
  await page.getByRole('button',{name:'Aircraft support',exact:true}).click();
  await page.getByRole('button',{name:'Inspect QA-CIV-1',exact:true}).click();
  await page.getByLabel('Reported cargo allowance (kg)',{exact:true}).fill('100');
  await page.getByLabel('Support source',{exact:true}).fill('Fictional operator support log');
  for(const name of ['Crew report','Maintenance report','Fuel report']) await page.getByLabel(name,{exact:true}).selectOption('confirmed');
  await page.getByLabel('Support change reason',{exact:true}).fill('Fictional current support evidence.');

  await page.getByRole('button',{name:'Save support evidence',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Dated aircraft support report saved'}).waitFor();
  await page.getByRole('cell',{name:'100 kg',exact:true}).waitFor();
  await capture('aircraft-support');
  await page.getByRole('button',{name:'Workflow planner',exact:true}).click();
  check(await page.getByLabel('Workflow title',{exact:true}).inputValue()==='Fictional river relief preparation','Tab switch lost preparation form');
  await page.getByRole('button',{name:'Evaluate response workflow',exact:true}).click();
  await page.getByRole('heading',{name:'Ready for coordinator review',exact:true}).waitFor();

  await capture('response-builder');
  await page.getByRole('button',{name:'Save preparation draft',exact:true}).click();
  await page.getByLabel('Coordinator review reason',{exact:true}).fill('Fictional coordinator checked this preparation example.');
  await page.getByRole('button',{name:'Record coordinator review',exact:true}).click();
  await page.getByRole('heading',{name:'Coordinator review recorded',exact:true}).waitFor();
  await capture('response-preparation', page.locator('.response-result'));
  const balance = await get('/inventory/position?item_id='+item.id+'&location_id='+store.id);
  check(balance.position.available === '100' && balance.records.length === 1, 'Preparation changed stock');
  const phoneContext = await page.context().browser().newContext({
    storageState: await page.context().storageState(),
    viewport:{width:390,height:844},hasTouch:true,isMobile:true,deviceScaleFactor:1,
  });
  try {
    const phone = await phoneContext.newPage();
    phone.on('pageerror', error=>errors.push(error.message));
    await phone.goto(origin+'/#response');
    await phone.getByRole('button',{name:'Workflow planner',exact:true}).click();
    await phone.locator('.response-plan-row').first().click();
    await phone.getByRole('heading',{name:'Coordinator review recorded',exact:true}).waitFor();
    await phone.evaluate(async()=>{await document.fonts.ready;document.activeElement?.blur();});
    await phone.locator('.response-result').evaluate(el=>scrollTo(0,el.getBoundingClientRect().top+scrollY-85));
    const layout=await phone.evaluate(()=>({width:document.documentElement.clientWidth,content:document.documentElement.scrollWidth}));
    check(layout.content<=layout.width,'Response phone page overflow');
    await phone.screenshot({path:'docs/images/response-mobile.png'});
  } finally { await phoneContext.close(); }
  check(errors.length===0,errors.join('; '));
  return {captures:6,disposableFictionalWorkspace:true,proposedCargoKg:80,proposedPacks:40,stockUnchanged:true,browserExceptions:0};
}
