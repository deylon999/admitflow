import { expect, it } from 'vitest';
import fixture from './fixtures/scenario.json' with { type: 'json' };
import { assertScenarioOrder, parseScenario, parseScenarioPage } from '../src/lib/scenario-contracts';
it('preserves conditional bounds and stored explanation without calculating a forecast', () => {
  const value=parseScenario(fixture);expect(value.result?.numbers?.currentLower).toBe(2);expect(value.result?.officialResultAvailable).toBe(false);
  expect(value.explanation?.summary).toContain('При вашем согласии');
});
it.each([{officialResultAvailable:true},{modelVersion:'unverified-v2'},{state:'within'},{numbers:{...fixture.result.numbers,currentUpper:4}},{numbers:{...fixture.result.numbers,consentYesAbove:99}}])('refuses contradictory or unsupported numeric results %s', changes=>{
  expect(()=>parseScenario({...fixture,result:{...fixture.result,...changes}})).toThrow();
});
it('rejects mixed identities, duplicate pages and invalid cursors',()=>{
 const a=parseScenario(fixture),b=parseScenario({...fixture,id:'scenario-a'});
 expect(()=>assertScenarioOrder([a,b])).not.toThrow();
 expect(()=>assertScenarioOrder([a,a])).toThrow();
 expect(()=>assertScenarioOrder([a,{...b,sourceId:'foreign-source'}])).toThrow();
 expect(()=>parseScenarioPage({items:[fixture],total:1,nextCursor:'other'})).toThrow();
 expect(()=>parseScenario({...fixture,available:false})).toThrow();
});
