#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple License Mock Tool for BT-Panel
Chỉ sử dụng thư viện Python chuẩn, không cần cài thêm gì
"""

import os
import sys
import json
import time
import hashlib
import socket
import subprocess
import shutil
from datetime import datetime, timedelta

class SimpleLicenseMock:
    def __init__(self):
        self.panel_path = "/www/server/panel"
        self.data_path = os.path.join(self.panel_path, "data")
        self.userinfo_file = os.path.join(self.data_path, "userInfo.json")
        self.backup_file = os.path.join(self.data_path, "userInfo.json.backup")
        self.plugin_cache = os.path.join(self.data_path, "plugin_bin.pl")
        
    def get_mac_address(self):
        """Lấy MAC address đơn giản"""
        try:
            result = subprocess.run(['cat', '/sys/class/net/eth0/address'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Fallback
        try:
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'link/ether' in line:
                    return line.split()[1]
        except:
            pass
        
        return "00:11:22:33:44:55"  # Default MAC
    
    def get_hostname(self):
        """Lấy hostname"""
        try:
            return socket.gethostname()
        except:
            return "bt-panel"
    
    def get_cpu_info(self):
        """Lấy thông tin CPU đơn giản"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(':')[1].strip()
        except:
            pass
        return "Unknown CPU"
    
    def set_file_immutable(self, file_path):
        """Set file as immutable using chattr +i"""
        try:
            result = subprocess.run(['chattr', '+i', file_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"⚠ Warning: chattr +i failed for {file_path}: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠ Warning: Could not set immutable {file_path}: {e}")
            return False
    
    def remove_file_immutable(self, file_path):
        """Remove immutable attribute using chattr -i"""
        try:
            result = subprocess.run(['chattr', '-i', file_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                # Not an error if file doesn't have immutable attribute
                return True
        except Exception as e:
            print(f"⚠ Warning: Could not remove immutable {file_path}: {e}")
            return False
    
    def check_file_immutable(self, file_path):
        """Check if file has immutable attribute"""
        try:
            result = subprocess.run(['lsattr', file_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return 'i' in result.stdout.lower()
            return False
        except:
            return False
    
    def md5(self, text):
        """Tạo MD5 hash"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def generate_server_id(self):
        """Tạo server ID như trong code gốc"""
        s1 = self.get_mac_address() + self.get_hostname()
        s2 = self.get_cpu_info()
        return self.md5(s1) + self.md5(s2)
    
    def generate_mock_userinfo(self):
        """Tạo mock userInfo.json"""
        server_id = self.generate_server_id()
        
        # Tạo token giả với format chuẩn hơn để tránh verification error
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "uid": 12345,
            "username": "debug_user", 
            "email": "debug@example.com",
            "exp": int(time.time()) + 86400 * 365,  # 1 năm
            "iat": int(time.time()),
            "server_id": server_id,
            "plan": "pro",
            "features": ["all"]
        }
        
        # Tạo JWT giả với signature mạnh hơn
        import base64
        header_json = json.dumps(header, separators=(',', ':'))
        payload_json = json.dumps(payload, separators=(',', ':'))
        
        header_b64 = base64.urlsafe_b64encode(header_json.encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
        
        # Tạo signature từ server_id để consistent
        signing_input = f"{header_b64}.{payload_b64}"
        signature_base = self.md5(f"{signing_input}.{server_id}.bt_panel_secret")
        signature = base64.urlsafe_b64encode(signature_base.encode()).decode().rstrip('=')[:43]
        
        mock_token = f"{header_b64}.{payload_b64}.{signature}"
        
        userinfo = {
            "id": 12345,
            "uid": 12345,
            "username": "debug_user",
            "email": "debug@example.com", 
            "phone": "",
            "avatar": "",
            "token": mock_token,
            "server_id": server_id,
            "access_key": self.md5(f"access_{server_id}")[:32],
            "secret_key": self.md5(f"secret_{server_id}")[:32],
            "login_time": int(time.time()),
            "expire_time": int(time.time()) + 86400 * 365,
            "plan": "pro",
            "permissions": ["all"],
            "is_mock": True  # Indicator that this is mock data
        }
        
        return userinfo
    
    def generate_license_cache(self):
        """Tạo cache license như hệ thống thật"""
        mac = self.get_mac_address()
        p_token = f"bmac_{self.md5(mac)}"
        
        # PRO license expire trong 1 năm
        pro_expire = int(time.time()) + 86400 * 365
        
        # Tạo cache files
        cache_file = f"/tmp/{p_token}"
        time_file = f"/tmp/{p_token}.time"
        
        with open(cache_file, 'w') as f:
            f.write(str(pro_expire))
        
        with open(time_file, 'w') as f:
            f.write(str(int(time.time())))
        
        # Set cache files immutable
        self.set_file_immutable(cache_file)
        self.set_file_immutable(time_file)
        
        print(f"✓ Created license cache (immutable): {cache_file}")
        return p_token
    
    def generate_plugin_cache(self):
        """Tạo mock plugin cache với PRO enabled (readonly)"""
        mock_plugin_data = {
            "status": True,
            "pro": int(time.time()) + 86400 * 365,  # PRO expire in 1 year
            "ltd": -1,  # No enterprise
            "list": {
                "data": [],
                "page": ""
            },
            "msg": "Mock PRO license active"
        }
        
        with open(self.plugin_cache, 'w') as f:
            json.dump(mock_plugin_data, f)
        
        # Set plugin cache readonly
        os.chmod(self.plugin_cache, 0o444)
        
        print(f"✓ Created plugin cache (readonly): {self.plugin_cache}")
    
    def generate_plugin_cache_writable(self):
        """Tạo mock plugin cache với PRO enabled (writable để BT-Panel có thể update)"""
        # KHÔNG tạo plugin cache ở đây để tránh conflict
        # Để BT-Panel tự tạo và quản lý cache này
        print(f"ℹ Skipped plugin cache creation - let BT-Panel manage it")
    
    def backup_original(self):
        """Backup file gốc"""
        if os.path.exists(self.userinfo_file) and not os.path.exists(self.backup_file):
            shutil.copy2(self.userinfo_file, self.backup_file)
            print(f"✓ Backed up original: {self.backup_file}")
        elif os.path.exists(self.backup_file):
            print(f"ℹ Backup already exists: {self.backup_file}")
    
    def apply_mock(self):
        """Apply mock license"""
        print("🚀 Applying mock PRO license...")
        
        # Ensure data directory exists
        os.makedirs(self.data_path, exist_ok=True)
        
        # Backup original
        self.backup_original()
        
        # Generate mock userinfo
        userinfo = self.generate_mock_userinfo()
        with open(self.userinfo_file, 'w') as f:
            json.dump(userinfo, f, indent=2)
        
        # Set userInfo as immutable to prevent modification
        self.set_file_immutable(self.userinfo_file)
        print(f"✓ Created mock userInfo (immutable): {self.userinfo_file}")
        
        # Generate license cache
        p_token = self.generate_license_cache()
        
        # Skip plugin cache - let BT-Panel manage it
        self.generate_plugin_cache_writable()
        
        print("✅ Mock PRO license applied successfully!")
        print(f"📋 Server ID: {userinfo['server_id']}")
        print(f"🎫 Token: {p_token}")
        print(f"🔒 UserInfo protected with immutable attribute")
        
        return True
    
    def remove_mock(self):
        """Remove mock và restore original"""
        print("🔄 Removing mock license...")
        
        # Remove immutable from userInfo before restore
        if os.path.exists(self.userinfo_file):
            self.remove_file_immutable(self.userinfo_file)
        
        # Restore original userInfo
        if os.path.exists(self.backup_file):
            shutil.copy2(self.backup_file, self.userinfo_file)
            print(f"✓ Restored original: {self.userinfo_file}")
        else:
            if os.path.exists(self.userinfo_file):
                os.remove(self.userinfo_file)
                print(f"✓ Removed mock: {self.userinfo_file}")
        
        # Clean cache files
        mac = self.get_mac_address()
        p_token = f"bmac_{self.md5(mac)}"
        cache_files = [
            f"/tmp/{p_token}",
            f"/tmp/{p_token}.time"
        ]
        
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                try:
                    # Remove immutable before delete
                    self.remove_file_immutable(cache_file)
                    os.remove(cache_file)
                    print(f"✓ Removed cache: {cache_file}")
                except:
                    print(f"⚠ Warning: Could not remove {cache_file}")
        
        # Clean plugin cache if exists (usually not created by us anymore)
        if os.path.exists(self.plugin_cache):
            try:
                os.remove(self.plugin_cache)
                print(f"✓ Removed plugin cache: {self.plugin_cache}")
            except:
                print(f"ℹ Plugin cache managed by BT-Panel")
        
        print("✅ Mock license removed successfully!")
        return True
    
    def status(self):
        """Kiểm tra trạng thái mock"""
        print("📊 Mock License Status:")
        print("=" * 50)
        
        # Check userInfo
        if os.path.exists(self.userinfo_file):
            try:
                with open(self.userinfo_file, 'r') as f:
                    userinfo = json.load(f)
                
                if 'token' in userinfo:
                    print(f"✅ UserInfo: MOCK ACTIVE")
                    print(f"   User: {userinfo.get('username', 'N/A')}")
                    print(f"   Server ID: {userinfo.get('server_id', 'N/A')[:16]}...")
                    print(f"   Plan: {userinfo.get('plan', 'N/A')}")
                    
                    # Check file protection (immutable vs permissions)
                    if self.check_file_immutable(self.userinfo_file):
                        print(f"   Protection: IMMUTABLE ✅")
                    else:
                        file_stat = os.stat(self.userinfo_file)
                        file_mode = oct(file_stat.st_mode)[-3:]
                        if file_mode == '444':
                            print(f"   Protection: READONLY ✅")
                        else:
                            print(f"   Protection: WRITABLE ⚠️ (mode: {file_mode})")
                else:
                    print(f"🟡 UserInfo: ORIGINAL (no token)")
            except:
                print(f"❌ UserInfo: ERROR reading file")
        else:
            print(f"❌ UserInfo: NOT FOUND")
        
        # Check cache
        mac = self.get_mac_address()
        p_token = f"bmac_{self.md5(mac)}"
        cache_file = f"/tmp/{p_token}"
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    pro_expire = int(f.read().strip())
                
                if pro_expire > time.time():
                    expire_date = datetime.fromtimestamp(pro_expire).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"✅ License Cache: PRO ACTIVE")
                    print(f"   Expires: {expire_date}")
                    
                    # Check cache file protection (immutable vs permissions)
                    if self.check_file_immutable(cache_file):
                        print(f"   Protection: IMMUTABLE ✅")
                    else:
                        file_stat = os.stat(cache_file)
                        file_mode = oct(file_stat.st_mode)[-3:]
                        if file_mode == '444':
                            print(f"   Protection: READONLY ✅")
                        else:
                            print(f"   Protection: WRITABLE ⚠️")
                else:
                    print(f"❌ License Cache: EXPIRED")
            except:
                print(f"❌ License Cache: ERROR reading")
        else:
            print(f"❌ License Cache: NOT FOUND")
        
        # Check backup
        if os.path.exists(self.backup_file):
            print(f"✅ Backup: EXISTS")
        else:
            print(f"🟡 Backup: NOT FOUND")
        
        # Check data directory permissions
        if os.path.exists(self.data_path):
            try:
                dir_stat = os.stat(self.data_path)
                dir_mode = oct(dir_stat.st_mode)[-3:]
                if dir_mode == '755':
                    print(f"✅ Data Directory: WRITABLE (mode: {dir_mode}) - BT-Panel can operate")
                elif dir_mode == '555':
                    print(f"⚠️ Data Directory: READONLY (mode: {dir_mode}) - May cause issues!")
                else:
                    print(f"🟡 Data Directory: mode {dir_mode}")
            except:
                print(f"❌ Data Directory: ERROR checking permissions")
        
        print("=" * 50)
    
    def fix_permissions(self):
        """Fix directory permissions nếu có vấn đề"""
        print("🔧 Fixing permissions...")
        
        # Fix data directory
        try:
            os.chmod(self.data_path, 0o755)
            print(f"✓ Fixed data directory permissions: {self.data_path}")
        except Exception as e:
            print(f"❌ Could not fix data directory: {e}")
        
        # Ensure userInfo is readonly (if exists and is mock)
        if os.path.exists(self.userinfo_file):
            try:
                with open(self.userinfo_file, 'r') as f:
                    userinfo = json.load(f)
                if 'is_mock' in userinfo:
                    os.chmod(self.userinfo_file, 0o444)
                    print(f"✓ Protected userInfo.json (readonly)")
                else:
                    print(f"ℹ userInfo.json is original (not protected)")
            except:
                print(f"⚠ Could not check/fix userInfo.json")
        
        # Ensure plugin cache is writable (if exists)
        if os.path.exists(self.plugin_cache):
            try:
                os.chmod(self.plugin_cache, 0o644)
                print(f"✓ Plugin cache is writable")
            except:
                print(f"⚠ Could not fix plugin cache permissions")
        
        print("✅ Permission fix completed!")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 simple_license_mock.py apply     # Apply mock PRO license")
        print("  python3 simple_license_mock.py remove    # Remove mock license")
        print("  python3 simple_license_mock.py status    # Check status")
        print("  python3 simple_license_mock.py fix       # Fix directory permissions")
        return
    
    mock = SimpleLicenseMock()
    
    if sys.argv[1] == "apply":
        mock.apply_mock()
    elif sys.argv[1] == "remove":
        mock.remove_mock()
    elif sys.argv[1] == "status":
        mock.status()
    elif sys.argv[1] == "fix":
        mock.fix_permissions()
    else:
        print(f"Unknown command: {sys.argv[1]}")

if __name__ == "__main__":
    main()
