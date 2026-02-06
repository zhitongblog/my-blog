import { Waline } from '@waline/cloud-storage/d1';

export default {
  async fetch(request, env, ctx) {
    return Waline(request, env, ctx);
  }
};