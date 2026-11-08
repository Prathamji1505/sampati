async page => {
  await page.goto('http://127.0.0.1:5173/#demo/overview');
  await page.getByRole('heading',{name:'Relief work awaiting attention',exact:true}).waitFor();
  await page.getByRole('heading',{name:'Reviewed needs still awaiting delivery',exact:true}).waitFor();
  const data=await(await page.request.get('http://127.0.0.1:5173/api/demo/overview/relief')).json();
  if(data.needs[0].remaining!=='30')throw new Error('Demo remainder must reflect source-confirmed arrivals');
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export relief overview',exact:true}).click();
  if((await download).suggestedFilename()!=='sampati-relief-overview.json')throw new Error('Wrong overview export');
  for(const width of [1440,1024,390,320]){await page.setViewportSize({width,height:1000});await page.evaluate(async()=>{await document.fonts.ready;scrollTo(0,0)});if(!(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)))throw new Error('Overview overflow '+width);await page.screenshot({path:'.impeccable/review/relief-overview-'+width+'.png',fullPage:true})}
  await page.setViewportSize({width:1440,height:1000});await page.getByRole('button',{name:'Open inbox',exact:true}).click();await page.getByRole('heading',{name:'Automation inbox',exact:true}).waitFor();
  return {passed:['correct demo remaining quantity','handover export','queue navigation','four-width containment']};
}
