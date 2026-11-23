// Read-only compiled-UI recovery check, run after browser-response.js in QA.
async page => {
  const origin='http://127.0.0.1:8000';
  const check=(condition,message)=>{if(!condition)throw new Error(message)};
  const browser=page.context().browser();
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const recovery=await context.newPage();
  try {
    await recovery.route('**/assets/ResponsePlanner-*.js',route=>route.abort('failed'));
    await recovery.goto(origin+'/#demo/response');
    await recovery.getByRole('heading',{name:'The workspace tools could not load',exact:true}).waitFor();
    await recovery.screenshot({path:'.impeccable/review/response-module-error-desktop.png',fullPage:true});
    await recovery.setViewportSize({width:390,height:844});
    check(await recovery.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Recovery page overflows phone width');
    await recovery.screenshot({path:'.impeccable/review/response-module-error-mobile.png',fullPage:true});
    await recovery.setViewportSize({width:1440,height:1000});
    await recovery.getByRole('button',{name:'Aircraft & data',exact:true}).click();
    await recovery.getByRole('button',{name:/^Aircraft register/}).click();
    await recovery.getByRole('heading',{name:'Aircraft register',exact:true}).waitFor();
    await recovery.getByRole('button',{name:'Response preparation',exact:true}).click();
    await recovery.getByRole('button',{name:'Reload workspace',exact:true}).waitFor();
    await recovery.unroute('**/assets/ResponsePlanner-*.js');
    await recovery.getByRole('button',{name:'Reload workspace',exact:true}).click();
    await recovery.getByRole('heading',{name:'No warning reports yet',exact:true}).waitFor();
    return {passed:['missing module shows recoverable error','navigation remains usable','reload fetches current module','phone recovery page contains its content']};
  } finally {await context.close();}
}
