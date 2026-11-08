async page => {
  const errors=[];const listener=message=>{if(message.type()==='error')errors.push(message.text())};page.on('console',listener);
  await page.goto('http://127.0.0.1:8000/');await page.getByRole('heading',{name:'Sampati',exact:true}).waitFor();
  await page.getByRole('button',{name:'Read workspace guide',exact:true}).click();await page.getByRole('heading',{name:'Your workspace, explained',exact:true}).waitFor();
  await page.goto('http://127.0.0.1:8000/#demo/overview');await page.getByRole('heading',{name:'Reviewed needs still awaiting delivery',exact:true}).waitFor();
  await page.getByRole('button',{name:'Open inbox',exact:true}).click();await page.getByRole('button',{name:'Inspect file DEMO-INTAKE-001',exact:true}).click();await page.getByRole('heading',{name:'Intake history',exact:true}).waitFor();
  if(errors.length)throw new Error(errors.join('; '));page.off('console',listener);
  return {passed:['compiled interface and API from port8000','standalone guide','relief overview','demo intake evidence','no console errors']};
}
