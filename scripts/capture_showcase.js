// Read-only captures of shared fictional records for the repository/profile.
async page => {
  const origin='http://127.0.0.1:8000';
  const get=async path=>(await page.request.get(origin+'/api/demo'+path)).json();
  const before={workspace:await get('/workspace'),relief:await get('/relief-requests'),stock:await get('/inventory'),shipments:await get('/deliveries'),intake:await get('/automation/inbox')};
  const errors=[];const onError=message=>{if(message.type()==='error')errors.push(message.text())};page.on('console',onError);
  const settle=()=>page.evaluate(async()=>{await document.fonts.ready;document.activeElement?.blur();scrollTo(0,0);await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))});
  await page.setViewportSize({width:1440,height:1040});
  const scenes=[['relief-overview','overview','Relief work awaiting attention'],['incident-review','incidents','Incident review'],['aid-inventory','inventory','Aid inventory'],['delivery-tracking','deliveries','Delivery tracking'],['automation-inbox','automation','Automation inbox']];
  for(const [name,route,title] of scenes){
    await page.goto(origin+'/#demo/'+route);await page.getByRole('heading',{name:title,exact:true}).waitFor();
    if(route==='overview')await page.getByRole('heading',{name:'Reviewed needs still awaiting delivery',exact:true}).waitFor();
    if(route==='incidents')await page.getByRole('button',{name:/DEMO/}).first().waitFor();
    if(route==='inventory')await page.locator('.inventory-table tbody tr').first().waitFor();
    if(route==='deliveries')await page.getByRole('button',{name:'Open DEMO-SHIP-001 shipment',exact:true}).waitFor();
    if(route==='automation')await page.getByRole('button',{name:'Inspect file DEMO-INTAKE-001',exact:true}).waitFor();
    await settle();await page.screenshot({path:'docs/images/'+name+'.png'});
  }
  await page.getByRole('button',{name:'Inspect file DEMO-INTAKE-001',exact:true}).click();await page.getByRole('heading',{name:'Intake history',exact:true}).waitFor();await settle();await page.screenshot({path:'docs/images/intake-evidence.png'});
  await page.goto(origin+'/#demo/deliveries');await page.getByRole('button',{name:'Request follow-up',exact:true}).click();await page.getByRole('cell',{name:'30 kits',exact:true}).waitFor();await settle();await page.screenshot({path:'docs/images/remaining-needs.png'});
  const phoneContext=await page.context().browser().newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,deviceScaleFactor:1});
  const phone=await phoneContext.newPage();await phone.goto(origin+'/#demo/automation');await phone.getByRole('button',{name:'Inspect file DEMO-INTAKE-001',exact:true}).waitFor();await phone.evaluate(async()=>{await document.fonts.ready;scrollTo(0,0)});await phone.screenshot({path:'docs/images/relief-mobile.png'});await phoneContext.close();
  const after=await get('/workspace');if(after.revision!==before.workspace.revision||after.imports.length!==before.workspace.imports.length)throw new Error('Captures changed accepted demo data');
  for(const [key,path] of [['relief','/relief-requests'],['stock','/inventory'],['shipments','/deliveries'],['intake','/automation/inbox']])if((await get(path)).total!==before[key].total)throw new Error('Capture changed '+key+' records');
  page.off('console',onError);if(errors.length)throw new Error(errors.join('; '));
  return {captures:8,fictionalDemoOnly:true,writes:0,consoleErrors:0};
}
