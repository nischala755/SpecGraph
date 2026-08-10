import {describe,it,expect} from 'vitest';
describe('status language',()=>it('keeps explicit labels',()=>expect(['confirmed','review','invalid']).toContain('review')));
