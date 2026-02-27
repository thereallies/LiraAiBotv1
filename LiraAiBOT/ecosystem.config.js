module.exports = {
  apps: [{
    name: 'liraai-multiassistent',
    script: 'backend/main.py',
    interpreter: '/root/liraai-multiassistent/venv/bin/python3',
    cwd: '/root/liraai-multiassistent',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    error_file: '/root/liraai-multiassistent/logs/pm2-error.log',
    out_file: '/root/liraai-multiassistent/logs/pm2-out.log',
    log_file: '/root/liraai-multiassistent/logs/pm2-combined.log',
    time: true,
    merge_logs: true
  }]
};

