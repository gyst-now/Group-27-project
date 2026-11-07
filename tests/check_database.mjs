import {PGlite} from '@electric-sql/pglite';
import {vector} from '@electric-sql/pglite-pgvector';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db = new PGlite({extensions:{vector}});
await db.exec('create role anon; create role authenticated; create role service_role bypassrls;');
await db.exec(await readFile(new URL('../supabase/migrations/0001_catalog_rag.sql', import.meta.url),'utf8'));
const embedding=JSON.stringify([1,...Array(1535).fill(0)]);
const chunks=JSON.stringify([{id:'known',course_code:'CS 124',heading:'CS 124',content:'Introduction to Computer Science',chunk_order:0,embedding}]);
const url='https://catalog.illinois.edu/courses-of-instruction/cs/';
for(let i=0;i<2;i++) await db.query('select catalog_replace_source($1,$2,$3,$4::jsonb)',[url,'hash','2026-27',chunks]);
assert.equal((await db.query('select count(*)::int as n from catalog_chunks')).rows[0].n,1);
let match=await db.query('select * from match_catalog_chunks($1::extensions.vector,5,$2)',[embedding,'2026-27']);
assert.equal(match.rows[0].id,'known'); assert.equal(match.rows[0].similarity,1);
assert.equal((await db.query('select * from match_catalog_chunks($1::extensions.vector,5,$2)',[embedding,'2025-26'])).rows.length,0);
assert.equal((await db.query('select * from catalog_exact_chunks($1,$2)',[['CS 124'],'2026-27'])).rows[0].id,'known');
try {await db.query('select catalog_replace_source($1,$2,$3,$4::jsonb)',[url,'bad','2026-27',JSON.stringify([{id:'broken',embedding:'[1,2]'}])]);assert.fail('must fail');}catch(e){assert.notEqual(e.message,'must fail');}
assert.equal((await db.query('select count(*)::int as n from catalog_chunks')).rows[0].n,1);
assert.equal((await db.query("select catalog_take_budget('ip',1,200) as ok")).rows[0].ok,true);
assert.equal((await db.query("select catalog_take_budget('ip',1,200) as ok")).rows[0].ok,false);
await db.exec('set role anon');
try {await db.query('select * from catalog_chunks');assert.fail('anon must fail');}catch(e){assert.notEqual(e.message,'anon must fail');}
try {await db.query('select * from match_catalog_chunks($1::extensions.vector,5,$2)',[embedding,'2026-27']);assert.fail('rpc must fail');}catch(e){assert.notEqual(e.message,'rpc must fail');}
await db.exec('reset role');
await db.query("delete from catalog_chunks where id='known'");
assert.equal((await db.query('select count(*)::int as n from catalog_chunks')).rows[0].n,0);
console.log('PASS: migration, vector search, edition filter, exact lookup, idempotency, replacement rollback, budget denial, anon table/RPC denial, deletion. Disposable PGlite + pgvector; existing Supabase untouched.');
await db.close();
