# 🧩 Development Roadmap (Build Order)

Follow this order to build features incrementally:

## Phase 1: Foundations

### User Auth
- JWT (access + refresh tokens)
- Roles: user, admin, superuser

### Channels
- Create channel (public/private)
- Membership model (owner, admin, moderator, member)
- Role permissions (mute/unmute, post, moderate)

---

## Phase 2: Content Posting

### Upload Media
- Videos, Shorts, Audios, Images
- Store in S3/MinIO
- Save metadata in Postgres

### Background Jobs
- Celery worker with Redis
- FFmpeg jobs for transcoding + thumbnails

### Playback
- Serve via CDN (HLS/DASH)
- Basic player integration

---

## Phase 3: Live Streaming

### Streaming Setup
- Nginx-RTMP for ingest (rtmp://server/live/{stream_key})
- FFmpeg pipeline → HLS segments
- Store playlists in S3/CDN

### FastAPI Endpoints
- Start/Stop stream
- Generate stream keys
- Mark content live/ended

---

## Phase 4: Chat & Realtime

### WebSocket Chat
- FastAPI WebSocket endpoint per channel
- Redis pub/sub for scaling
- Mute/unmute members

### Moderation Tools
- Delete messages
- Pin posts
- Ban user from chat

---

## Phase 5: Classes & Groups

### Channel Classes
- Schedule/start a class session
- Members join via chat/voice
- Record or livestream classes

### Group Features
- Add/remove members
- Role-based permissions
- Telegram-like "muted/unmuted" member states

---

## Phase 6: Discovery & Analytics

### Search
- ElasticSearch/Meilisearch for content, channels

### Recommendations
- Track views, likes, subscriptions
- Simple popular/recommended feeds

### Analytics
- Viewer counts, watch time, channel stats

---

## Phase 7: Extras

### Downloads
- Allow content download (respect visibility/roles)

### Sharing
- Generate short links, embed codes

### Security
- Signed URLs for private content
- Rate limiting, spam prevention

### Scaling
- CDN, multi-region ingest servers
- Monitoring (Prometheus + Grafana)
