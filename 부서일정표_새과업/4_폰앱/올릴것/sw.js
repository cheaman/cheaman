// 홈 화면 설치용 일꾼 — 파일을 담아 두지 않는다 (담아 두면 껍데기를 고쳐도 폰에 옛것이 남음)
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
