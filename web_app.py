from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import json
import io
import base64
import math
import random
import tempfile
import os
import traceback
from datetime import datetime, timedelta

# Import logic từ file gốc với fallback
try:
    # ƯU TIÊN: Sử dụng engine Version3 đã được kiểm chứng
    from backtest_gridsearch_slbe_ts_Version3 import (
        simulate_trade, grid_search_parallel,
        load_trade_csv as load_trade_csv_file,
        load_candle_csv as load_candle_csv_file, 
        get_trade_pairs as get_trade_pairs_file
    )
    print("✅ CHẾ ĐỘ NÂNG CAO ĐÃ KÍCH HOẠT: Mô phỏng đầy đủ BE + TS từ Version3")
    print("🔥 ENGINE THỰC CHIẾN: Logic SL + Breakeven + Trailing Stop đã sẵn sàng")
    ADVANCED_MODE = True
            
except ImportError as e:
    print(f"⚠️ Không thể tải module nâng cao: {e}")
    print("🔄 Chuyển sang chế độ chỉ SL...")
    ADVANCED_MODE = False
    
    # Fallback functions
    def simulate_trade(*args, **kwargs):
        return None, ["Mô phỏng nâng cao không khả dụng"]
    
    def grid_search_parallel(trade_pairs, df_candle, sl_list, be_list, ts_trig_list, ts_step_list, opt_type):
        """
        Triển khai dự phòng khi module nâng cao không khả dụng.
        Thay vì trả về mảng rỗng, sử dụng dự phòng chỉ SL với tham số BE/TS mặc định.
        """
        print("⚠️ grid_search_parallel: Module nâng cao không khả dụng, sử dụng dự phòng chỉ SL")
        print("🚨 CẢNH BÁO: Đây là chế độ CHỈ SL, không phải mô phỏng thực tế BE+TS!")
        
        # Sử dụng giá trị trung bình từ các dải BE/TS làm tham số cố định
        be_default = be_list[len(be_list)//2] if be_list else 0.5
        ts_trig_default = ts_trig_list[len(ts_trig_list)//2] if ts_trig_list else 0.5  
        ts_step_default = ts_step_list[len(ts_step_list)//2] if ts_step_list else 0.5
        
        # Gọi hàm dự phòng chỉ SL với tham số BE/TS mặc định
        sl_min = min(sl_list) if sl_list else 0
        sl_max = max(sl_list) if sl_list else 0
        sl_step = sl_list[1] - sl_list[0] if len(sl_list) > 1 else 1.0
        
        return grid_search_sl_fallback(trade_pairs, df_candle, sl_min, sl_max, sl_step, opt_type,
                                      be_default, ts_trig_default, ts_step_default)
        
    def load_trade_csv_file(*args, **kwargs):
        raise ImportError("Tải file trade không khả dụng")
    
    def load_candle_csv_file(*args, **kwargs):
        raise ImportError("Tải file nến không khả dụng")
    
    def get_trade_pairs_file(*args, **kwargs):
        raise ImportError("Tạo cặp trade không khả dụng")

app = Flask(__name__)

# Global variable to track optimization progress
optimization_status = {
    'running': False,
    'start_time': None,
    'total_combinations': 0,
    'current_progress': 0,
    'estimated_completion': None,
    'status_message': 'Ready'
}

def convert_to_serializable(obj):
    """Convert numpy/pandas types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        val = float(obj)
        # Handle infinity values for JSON serialization
        if np.isinf(val):
            # For advanced metrics, allow reasonable infinity values
            if abs(val) > 1e6:
                print(f"⚠️ WARNING: Very large infinity in convert_to_serializable: {val}")
                return 999999.0 if val > 0 else -999999.0
            else:
                return val  # Keep reasonable infinity values for metrics
        elif np.isnan(val):
            return 0.0
        return val
    elif isinstance(obj, float):
        # Handle Python float infinity/nan
        if np.isinf(obj):
            if abs(obj) > 1e6:
                print(f"⚠️ WARNING: Very large Python float infinity: {obj}")
                return 999999.0 if obj > 0 else -999999.0
            else:
                return obj  # Keep reasonable infinity values
        elif np.isnan(obj):
            return 0.0
        return obj
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

def safe_float_parse(form_data, key, default):
    """Safely parse float from form data, handling empty strings and invalid values"""
    try:
        value = form_data.get(key, default)
        if isinstance(value, str):
            value = value.strip()  # Remove whitespace
            if not value:  # Empty or whitespace-only string
                return float(default)
        return float(value)
    except (ValueError, TypeError):
        return float(default)

def safe_float(value):
    """Safely convert to float, handling infinity and NaN"""
    try:
        val = float(value)
        if np.isinf(val):
            # For advanced metrics, infinity might be valid (e.g., recovery factor when DD=0)
            # Only convert very large values that could break JSON
            if abs(val) > 1e6:
                print(f"⚠️ WARNING: Very large infinity value detected in safe_float: {value}")
                return 999999.0 if val > 0 else -999999.0
            else:
                return val  # Keep reasonable infinity values
        elif np.isnan(val):
            return 0.0
        return val
    except (TypeError, ValueError):
        return 0.0

def safe_int(value):
    """Safely convert to int, handling infinity and NaN"""
    try:
        val = float(value)
        if np.isinf(val):
            print(f"⚠️ WARNING: Infinity value detected in safe_int: {value}")
            return 0  # Return 0 instead of 999999 for better data quality
        elif np.isnan(val):
            return 0
        return int(val)
    except (TypeError, ValueError):
        return 0

# Import các functions từ script gốc
def normalize_trade_date(s):
    """Normalize trade date with support for multiple formats"""
    try:
        # Thử format 1: YYYY-MM-DD HH:MM (ACEUSDT/TradingView/BOME format)
        dt = pd.to_datetime(s, format='%Y-%m-%d %H:%M', errors='coerce')
        if not pd.isna(dt):
            # For simplicity, treat all YYYY-MM-DD format as UTC
            if dt.tz is None:
                dt = dt.tz_localize('UTC').tz_localize(None)
            return dt
    except:
        pass
    
    try:
        # Thử format 2: MM/DD/YYYY HH:MM (Legacy BTC format)
        dt = pd.to_datetime(s, format='%m/%d/%Y %H:%M', errors='coerce')
        if not pd.isna(dt):
            # Assume Bangkok timezone for old MM/DD/YYYY format, convert to UTC
            if dt.tz is None:
                dt = dt.tz_localize('Asia/Bangkok').tz_convert('UTC').tz_localize(None)
            return dt
    except:
        pass
    
    try:
        # Fallback: Auto-detect format
        dt = pd.to_datetime(s, errors='coerce')
        if not pd.isna(dt):
            if dt.tz is None:
                # Default to UTC timezone for unknown formats
                dt = dt.tz_localize('UTC').tz_localize(None)
            else:
                # Convert existing timezone to UTC
                dt = dt.tz_convert('UTC').tz_localize(None)
            return dt
    except Exception as e:
        print(f"Warning: Error parsing trade date '{s}': {e}")
        pass
    
    return pd.NaT

def normalize_candle_date(s):
    """Normalize candle date with proper timezone handling for Vietnam timezone"""
    try:
        dt = pd.to_datetime(s, errors='coerce')
        if not pd.isna(dt):
            if dt.tz is not None:
                # Keep Vietnam timezone (+7) and then remove tz info for consistency with trade data
                # Most trade data from TradingView is in Vietnam time
                dt = dt.tz_localize(None)  # Remove timezone but keep the time value
            return dt
    except Exception as e:
        print(f"Warning: Error parsing candle date '{s}': {e}")
        return pd.NaT
    
    return pd.NaT

def smart_read_csv(file_content):
    """Đọc CSV từ nội dung file"""
    try:
        df = pd.read_csv(io.StringIO(file_content), sep=",")
        if len(df.columns) == 1:
            df = pd.read_csv(io.StringIO(file_content), sep="\t")
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as e:
        print(f"Warning: CSV parsing with comma failed: {e}, trying tab separator")
        try:
            df = pd.read_csv(io.StringIO(file_content), sep="\t")
        except Exception as e2:
            print(f"Error: All CSV parsing methods failed: {e2}")
            raise ValueError(f"Cannot parse CSV content: {e2}")
    return df

def load_trade_csv_from_content(content):
    """Universal trade CSV loader using Version3 functions"""
    temp_path = None
    try:
        # 🔧 FORCE USE VERSION3 FUNCTIONS (with date format fix)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Use fixed Version3 load_trade_csv function
        from backtest_gridsearch_slbe_ts_Version3 import load_trade_csv
        df = load_trade_csv(temp_path)
        
        if len(df) == 0:
            raise ValueError('No valid trade data found after Version3 parsing')
        
        trades = len(df['trade'].unique())
        records = len(df)
        print(f"✅ Version3 trade loading: {records} records from {trades} trades")
        return df
        
    except Exception as e:
        print(f"⚠️ Version3 parser failed: {e}, falling back to legacy methods")
        return load_trade_csv_from_content_legacy(content)
    
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def load_trade_csv_from_content_legacy(content):
    df = smart_read_csv(content)
    
    # Clean column names
    df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_').replace('#', '').replace('&', '') for col in df.columns]
    
    # Smart column mapping
    column_mapping = {}
    
    # Map Trade column
    for col in ['trade_', 'trade_number', 'trade']:
        if col in df.columns:
            column_mapping[col] = 'trade'
            break
    
    # Map Price column  
    for col in ['price_usdt', 'price']:
        if col in df.columns:
            column_mapping[col] = 'price'
            break
    
    # Map Date/Time column - keep original names for proper routing
    if 'date_time' in df.columns:
        column_mapping['date_time'] = 'date_time'  # ACEUSDT format
    elif 'date' in df.columns:
        # Don't remap 'date' column for legacy format - keep it as 'date'
        pass  # Keep original 'date' column name for legacy format
    
    if column_mapping:
        df.rename(columns=column_mapping, inplace=True)
    
    # Detect data format based on available columns
    has_signal = 'signal' in df.columns
    has_pnl_usdt = 'pl_usdt' in df.columns  # P&L USDT becomes pl_usdt after cleaning
    has_quantity = 'quantity' in df.columns
    has_tradingview_cols = has_signal and (has_pnl_usdt or has_quantity)
    
    # Check if this is BOME data (even though it's TradingView format)
    # BOME data has very small prices (around 0.009xxx)
    has_small_prices = False
    price_col_for_detection = None
    
    # Look for price column after mapping
    for col in ['price', 'price_usdt']:
        if col in df.columns:
            price_col_for_detection = col
            break
    
    if price_col_for_detection:
        try:
            price_sample = pd.to_numeric(df[price_col_for_detection].head(10), errors='coerce').dropna()
            if len(price_sample) > 0:
                avg_price = price_sample.mean()
                has_small_prices = avg_price < 0.1  # BOME prices are around 0.009xxx
        except:
            pass
    
    if has_tradingview_cols:
        if has_small_prices:
            # BOME format (TradingView but different processing)
            return load_bome_format(df)
        else:
            # ACEUSDT format detected
            return load_aceusdt_format(df)
    else:
        # BTC/BOME format (legacy) - ensure 'date' column exists
        if 'date' not in df.columns:
            # Try to find date-like column
            date_candidates = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            if date_candidates:
                df['date'] = df[date_candidates[0]]
                print(f"🔍 LEGACY ROUTING: Created 'date' column from '{date_candidates[0]}'")
            else:
                raise ValueError(f"No date column found for legacy format! Available: {df.columns.tolist()}")
        return load_legacy_format(df)

def load_aceusdt_format(df):
    """Load ACEUSDT format data from TradingView Strategy Tester"""
    # Required columns for ACEUSDT format - check with original names
    required_cols = ['trade', 'type', 'signal']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"ACEUSDT format missing columns: {missing_cols}. Available: {df.columns.tolist()}")
    
    # Process datetime - try multiple column names
    date_col = None
    for col in ['date_time', 'date']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col is None:
        raise ValueError(f"No date column found in ACEUSDT format! Available columns: {df.columns.tolist()}")
    
    df['date'] = df[date_col].apply(normalize_trade_date)
    
    # Process price - use 'price_usdt' column or 'price'
    price_col = None
    for col in ['price_usdt', 'price']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        raise ValueError(f"No price column found in ACEUSDT format! Available columns: {df.columns.tolist()}")
    
    df['price'] = df[price_col].astype(str).str.replace(',', '').str.replace('"', '')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    # Filter for entry/exit trades
    # ACEUSDT format uses 'Type' column with values like "Entry long", "Exit short", etc.
    df = df[df['type'].str.lower().str.contains('entry') | df['type'].str.lower().str.contains('exit')]
    df = df.dropna(subset=['date', 'price'])
    
    return df

def load_bome_format(df):
    """Load BOME format data from TradingView Strategy Tester (small price format)"""
    # Required columns for BOME format - similar to ACEUSDT but different price handling
    required_cols = ['trade', 'type', 'signal']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"BOME format missing columns: {missing_cols}. Available: {df.columns.tolist()}")
    
    # Process datetime - try multiple column names (BOME uses 'date_time' after mapping)
    date_col = None
    for col in ['date_time', 'date']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col is None:
        raise ValueError(f"No date column found in BOME format! Available columns: {df.columns.tolist()}")
    
    df['date'] = df[date_col].apply(normalize_trade_date)
    
    # Process price - BOME has small prices (0.009xxx), need high precision
    price_col = None
    for col in ['price_usdt', 'price']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        raise ValueError(f"No price column found in BOME format! Available columns: {df.columns.tolist()}")
    
    df['price'] = df[price_col].astype(str).str.replace(',', '').str.replace('"', '')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    # Filter for entry/exit trades (same logic as ACEUSDT)
    df = df[df['type'].str.lower().str.contains('entry') | df['type'].str.lower().str.contains('exit')]
    df = df.dropna(subset=['date', 'price'])
    
    return df

def load_legacy_format(df):
    """Load legacy BTC/BOME format data"""
    print(f"🔄 Processing legacy format with {len(df)} rows")
    print(f"🔍 LEGACY START: Columns = {df.columns.tolist()}")
    print(f"🔍 LEGACY START: First 3 rows:\n{df.head(3).to_string()}")
    
    # Ensure we have 'date' column for legacy format
    if 'date' not in df.columns:
        # For legacy format, we should have 'date' column already
        # If we have 'date_time' (from mapping), use it as 'date'
        if 'date_time' in df.columns:
            df['date'] = df['date_time']
            print(f"🔍 LEGACY: Mapped 'date_time' -> 'date'")
        else:
            # Look for any date-like column
            date_candidates = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            if date_candidates:
                df['date'] = df[date_candidates[0]]
                print(f"🔍 LEGACY: Used '{date_candidates[0]}' as 'date'")
            else:
                raise ValueError(f"No date column found for legacy format! Available: {df.columns.tolist()}")
    
    # Check required columns for legacy format
    required_cols = ['trade', 'type', 'date', 'price']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"🔍 LEGACY: Available columns: {df.columns.tolist()}")
        print(f"🔍 LEGACY: Missing columns: {missing_cols}")
        raise ValueError(f"Legacy format missing columns: {missing_cols}! Available: {df.columns.tolist()}")
    
    print(f"🔍 LEGACY: Before date processing - sample dates: {df['date'].head(3).tolist()}")
    df['date'] = df['date'].apply(normalize_trade_date)
    print(f"🔍 LEGACY: After date processing - sample dates: {df['date'].head(3).tolist()}")
    
    print(f"🔍 LEGACY: Before price processing - sample prices: {df['price'].head(3).tolist()}")
    df['price'] = df['price'].astype(str).str.replace(',', '').str.replace('"', '')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    print(f"🔍 LEGACY: After price processing - sample prices: {df['price'].head(3).tolist()}")
    
    print(f"🔍 LEGACY: Before filtering - rows: {len(df)}")
    df = df[df['type'].str.lower().str.contains('entry') | df['type'].str.lower().str.contains('exit')]
    print(f"🔍 LEGACY: After entry/exit filter - rows: {len(df)}")
    df = df.dropna(subset=['date', 'price'])
    print(f"🔍 LEGACY: After dropna - rows: {len(df)}")
    
    if len(df) > 0:
        print(f"🔍 LEGACY FINAL: Sample processed row:\n{df.iloc[0].to_dict()}")
    
    print(f"✅ Legacy format processed: {len(df)} valid trade rows")
    return df

def load_candle_csv_from_content(content):
    """Load candle CSV using Version3 functions"""
    temp_path = None
    try:
        # 🔧 FORCE USE VERSION3 FUNCTIONS (with date format fix)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Use fixed Version3 load_candle_csv function
        from backtest_gridsearch_slbe_ts_Version3 import load_candle_csv
        df = load_candle_csv(temp_path)
        
        if len(df) == 0:
            raise ValueError('No valid candle data found after Version3 parsing')
        
        print(f"✅ Version3 candle loading: {len(df)} candles loaded")
        print(f"   Time range: {df['time'].min()} → {df['time'].max()}")
        return df
        
    except Exception as e:
        print(f"⚠️ Version3 candle parser failed: {e}")
        raise
    
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

def get_trade_pairs(df_trade):
    """Get trade pairs using Version3 function"""
    try:
        # 🔧 FORCE USE VERSION3 get_trade_pairs
        from backtest_gridsearch_slbe_ts_Version3 import get_trade_pairs as get_pairs_v3
        pairs, log = get_pairs_v3(df_trade)
        
        print(f"✅ Version3 trade pairs: {len(pairs)} pairs generated")
        if log:
            for msg in log[:5]:  # Show first 5 log messages
                print(f"   Log: {msg}")
        
        return pairs, log
        
    except Exception as e:
        print(f"⚠️ Version3 get_trade_pairs failed: {e}")
        # Fallback to original logic if needed
        return get_trade_pairs_legacy(df_trade)

def get_trade_pairs_legacy(df_trade):
    log = []
    pairs = []
    
    print(f"🔍 DEBUG: Processing {len(df_trade)} trade rows")
    print(f"🔍 DEBUG: Columns: {df_trade.columns.tolist()}")
    print(f"🔍 DEBUG: First 5 rows:")
    print(df_trade.head().to_string())
    
    # Detect data format
    # Check for TradingView format columns
    has_signal = 'signal' in df_trade.columns
    has_pnl_usdt = 'pl_usdt' in df_trade.columns  # P&L USDT becomes pl_usdt after cleaning
    has_quantity = 'quantity' in df_trade.columns
    has_tradingview_cols = has_signal and (has_pnl_usdt or has_quantity)
    
    # Check if this is BOME data (small prices)
    has_small_prices = False
    if 'price' in df_trade.columns:
        try:
            price_sample = pd.to_numeric(df_trade['price'].head(10), errors='coerce').dropna()
            if len(price_sample) > 0:
                avg_price = price_sample.mean()
                has_small_prices = avg_price < 0.1  # BOME prices are around 0.009xxx
        except:
            pass
    
    print(f"🔍 FORMAT DETECTION: signal={has_signal}, p&l_usdt={has_pnl_usdt}, quantity={has_quantity}, small_prices={has_small_prices}")
    
    if has_tradingview_cols:
        if has_small_prices:
            print(f"🔍 FORMAT: BOME (TradingView with small prices)")
            return get_bome_trade_pairs(df_trade)
        else:
            print(f"🔍 FORMAT: ACEUSDT (TradingView)")
            return get_aceusdt_trade_pairs(df_trade)
    else:
        print(f"🔍 FORMAT: Legacy (BTC/BOME)")
        return get_legacy_trade_pairs(df_trade)

def get_aceusdt_trade_pairs(df_trade):
    """Extract trade pairs from ACEUSDT TradingView format"""
    log = []
    pairs = []
    
    print(f"🔄 Processing ACEUSDT format with {len(df_trade)} rows")
    
    for trade_num in df_trade['trade'].unique():
        group = df_trade[df_trade['trade'] == trade_num]
        entry = group[group['type'].str.lower().str.contains('entry')]
        exit = group[group['type'].str.lower().str.contains('exit')]
        
        if len(entry) == 0 or len(exit) == 0:
            log.append(f"ACEUSDT Trade {trade_num}: thiếu Entry hoặc Exit, bỏ qua")
            continue
            
        entry_row = entry.iloc[0]
        exit_row = exit.iloc[0]
        
        # Determine side from Type column
        # "Entry long" = LONG, "Entry short" = SHORT
        entry_type = entry_row['type'].lower()
        if 'long' in entry_type:
            side = 'LONG'
        elif 'short' in entry_type:
            side = 'SHORT'
        else:
            # Fallback: check signal column
            signal = entry_row.get('signal', '').lower()
            side = 'LONG' if 'long' in signal else 'SHORT'
        
        # Debug first few trades
        if trade_num <= 3:
            print(f"🔍 ACEUSDT TRADE {trade_num} DEBUG:")
            print(f"   Entry row: {entry_row.to_dict()}")
            print(f"   Exit row: {exit_row.to_dict()}")
            print(f"   Entry type: {entry_row['type']}")
            print(f"   Exit type: {exit_row['type']}")
            print(f"   Side detected: {side}")
            print(f"   Entry price: {entry_row['price']}")
            print(f"   Exit price: {exit_row['price']}")
        
        pairs.append({
            'num': trade_num,
            'entryDt': entry_row.get('date', entry_row.get('date_time', entry_row.get('time', 'Unknown'))),
            'exitDt': exit_row.get('date', exit_row.get('date_time', exit_row.get('time', 'Unknown'))),
            'side': side,
            'entryPrice': entry_row['price'],
            'exitPrice': exit_row['price']
        })
        
    print(f"✅ ACEUSDT pairs extracted: {len(pairs)} valid pairs")
    return pairs, log

def get_bome_trade_pairs(df_trade):
    """Extract trade pairs from BOME TradingView format (small price precision)"""
    log = []
    pairs = []
    
    print(f"🔄 Processing BOME format with {len(df_trade)} rows")
    
    for trade_num in df_trade['trade'].unique():
        group = df_trade[df_trade['trade'] == trade_num]
        entry = group[group['type'].str.lower().str.contains('entry')]
        exit = group[group['type'].str.lower().str.contains('exit')]
        
        if len(entry) == 0 or len(exit) == 0:
            log.append(f"BOME Trade {trade_num}: thiếu Entry hoặc Exit, bỏ qua")
            continue
            
        entry_row = entry.iloc[0]
        exit_row = exit.iloc[0]
        
        # Determine side from Type column (same logic as ACEUSDT)
        entry_type = entry_row['type'].lower()
        if 'long' in entry_type:
            side = 'LONG'
        elif 'short' in entry_type:
            side = 'SHORT'
        else:
            # Fallback: check signal column
            signal = entry_row.get('signal', '').lower()
            side = 'LONG' if 'long' in signal else 'SHORT'
        
        # Debug first few trades with high precision for BOME
        if trade_num <= 3:
            print(f"🔍 BOME TRADE {trade_num} DEBUG:")
            print(f"   Entry row: {entry_row.to_dict()}")
            print(f"   Exit row: {exit_row.to_dict()}")
            print(f"   Entry type: {entry_row['type']}")
            print(f"   Exit type: {exit_row['type']}")
            print(f"   Side detected: {side}")
            print(f"   Entry price: {entry_row['price']:.8f}")  # Higher precision for BOME
            print(f"   Exit price: {exit_row['price']:.8f}")
        
        pairs.append({
            'num': trade_num,
            'entryDt': entry_row.get('date', entry_row.get('date_time', entry_row.get('time', 'Unknown'))),
            'exitDt': exit_row.get('date', exit_row.get('date_time', exit_row.get('time', 'Unknown'))),
            'side': side,
            'entryPrice': entry_row['price'],
            'exitPrice': exit_row['price']
        })
        
    print(f"✅ BOME pairs extracted: {len(pairs)} valid pairs")
    return pairs, log

def get_legacy_trade_pairs(df_trade):
    """Extract trade pairs from legacy BTC/BOME format"""
    log = []
    pairs = []
    
    print(f"🔄 Processing legacy format with {len(df_trade)} rows")
    
    for trade_num in df_trade['trade'].unique():
        group = df_trade[df_trade['trade']==trade_num]
        entry = group[group['type'].str.lower().str.contains('entry')]
        exit = group[group['type'].str.lower().str.contains('exit')]
        if len(entry)==0 or len(exit)==0:
            log.append(f"Legacy TradeNum {trade_num}: thiếu Entry hoặc Exit, bỏ qua")
            continue
        entry_row = entry.iloc[0]
        exit_row = exit.iloc[0]
        side = 'LONG' if 'long' in entry_row['type'].lower() else 'SHORT'
        
        # Debug first few trades to see actual data
        if trade_num <= 3:
            print(f"🔍 LEGACY TRADE {trade_num} DEBUG:")
            print(f"   Entry row: {entry_row.to_dict()}")
            print(f"   Exit row: {exit_row.to_dict()}")
            print(f"   Entry price: {entry_row['price']}")
            print(f"   Exit price: {exit_row['price']}")
            print(f"   Same price? {entry_row['price'] == exit_row['price']}")
        
        pairs.append({
            'num': trade_num,
            'entryDt': entry_row.get('date', entry_row.get('date_time', entry_row.get('time', 'Unknown'))),
            'exitDt': exit_row.get('date', exit_row.get('date_time', exit_row.get('time', 'Unknown'))),
            'side': side,
            'entryPrice': entry_row['price'],
            'exitPrice': exit_row['price']
        })
        
    print(f"✅ Legacy pairs extracted: {len(pairs)} valid pairs")
    return pairs, log

def calculate_original_performance(pairs):
    """Tính toán hiệu suất gốc của dữ liệu trade với các chỉ số nâng cao"""
    if not pairs:
        return None
    
    total_trades = len(pairs)
    win_trades = 0
    loss_trades = 0
    total_pnl = 0
    gross_profit = 0
    gross_loss = 0
    win_amounts = []
    loss_amounts = []
    pnl_list = []
    
    # Sort trades theo thời gian để tính drawdown
    sorted_pairs = sorted(pairs, key=lambda x: x['entryDt'])
    
    for pair in sorted_pairs:
        if pair['side'] == 'LONG':
            pnl_pct = (pair['exitPrice'] - pair['entryPrice']) / pair['entryPrice'] * 100
        else:  # SHORT
            pnl_pct = (pair['entryPrice'] - pair['exitPrice']) / pair['entryPrice'] * 100
        
        pnl_list.append(pnl_pct)
        total_pnl += pnl_pct
        
        if pnl_pct > 0:
            win_trades += 1
            gross_profit += pnl_pct
            win_amounts.append(pnl_pct)
        else:
            loss_trades += 1
            gross_loss += abs(pnl_pct)
            loss_amounts.append(pnl_pct)
    
    # Tính các chỉ số cơ bản
    winrate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    avg_trade = total_pnl / total_trades if total_trades > 0 else 0
    
    # Tính Max Drawdown
    cumulative_pnl = []
    running_total = 0
    for pnl in pnl_list:
        running_total += pnl
        cumulative_pnl.append(running_total)
    
    max_drawdown = 0
    peak = cumulative_pnl[0] if cumulative_pnl else 0
    for value in cumulative_pnl:
        if value > peak:
            peak = value
        drawdown = peak - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Tính Average Win/Loss
    avg_win = sum(win_amounts) / len(win_amounts) if win_amounts else 0
    avg_loss = sum(loss_amounts) / len(loss_amounts) if loss_amounts else 0
    
    # Tính Consecutive Wins/Losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_win_streak = 0
    current_loss_streak = 0
    
    for pnl in pnl_list:
        if pnl > 0:
            current_win_streak += 1
            current_loss_streak = 0
            max_consecutive_wins = max(max_consecutive_wins, current_win_streak)
        else:
            current_loss_streak += 1
            current_win_streak = 0
            max_consecutive_losses = max(max_consecutive_losses, current_loss_streak)
    
    # Tính Sharpe Ratio (đơn giản hoá)
    if len(pnl_list) > 1:
        std_dev = math.sqrt(sum([(x - avg_trade) ** 2 for x in pnl_list]) / (len(pnl_list) - 1))
        sharpe_ratio = avg_trade / std_dev if std_dev > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Tính Recovery Factor
    recovery_factor = total_pnl / max_drawdown if max_drawdown > 0 else float('inf') if total_pnl > 0 else 0
    
    return {
        'total_trades': total_trades,
        'win_trades': win_trades,
        'loss_trades': loss_trades,
        'total_pnl': total_pnl,
        'winrate': winrate,
        'profit_factor': safe_float(profit_factor),
        'avg_trade': avg_trade,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'max_drawdown': max_drawdown,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_consecutive_wins': max_consecutive_wins,
        'max_consecutive_losses': max_consecutive_losses,
        'sharpe_ratio': safe_float(sharpe_ratio),
        'recovery_factor': safe_float(recovery_factor)
    }

def create_original_baseline_details(trade_pairs):
    """
    CRITICAL HELPER: Create baseline details from ORIGINAL trade pairs
    This ensures we use actual tradelist data instead of simulation results
    """
    baseline_details = []
    for pair in trade_pairs:
        if pair['side'] == 'LONG':
            pnl_pct = (pair['exitPrice'] - pair['entryPrice']) / pair['entryPrice'] * 100
        else:  # SHORT
            pnl_pct = (pair['entryPrice'] - pair['exitPrice']) / pair['entryPrice'] * 100
        
        baseline_details.append({
            'entryDt': pair['entryDt'],
            'exitDt': pair['exitDt'],
            'pnlPct': pnl_pct,
            'num': pair['num'],
            'side': pair['side'],
            'entryPrice': pair['entryPrice'],  # Use original entry price
            'exitPrice': pair['exitPrice']    # Use original exit price
        })
    
    return baseline_details

def filter_trades_by_selection(pairs, max_trades=0, start_trade=1, selection_mode='sequence'):
    """Lọc trades theo tham số người dùng chọn"""
    if not pairs:
        return pairs
    
    # Sort theo mode
    if selection_mode == 'time':
        sorted_pairs = sorted(pairs, key=lambda x: x['entryDt'])
    elif selection_mode == 'random':
        sorted_pairs = pairs.copy()
        random.shuffle(sorted_pairs)
    else:  # sequence
        sorted_pairs = sorted(pairs, key=lambda x: x['num'])
    
    # Apply start_trade filter
    total_count = len(sorted_pairs)
    
    if start_trade < 0:
        # Số âm = bắt đầu từ cuối (ví dụ: -10 = 10 lệnh cuối)
        start_idx = max(0, total_count + start_trade)
        sorted_pairs = sorted_pairs[start_idx:]
    elif start_trade > 1:
        # Số dương = bắt đầu từ đầu (ví dụ: 5 = từ lệnh thứ 5)
        sorted_pairs = sorted_pairs[start_trade-1:]
    
    # Apply max_trades filter
    if max_trades > 0:
        sorted_pairs = sorted_pairs[:max_trades]
    
    return sorted_pairs

def find_candle_idx(dt, df_candle):
    if pd.isna(dt):
        return -1
    arr = df_candle['time'].values
    target_dt = np.datetime64(dt)
    min_time = arr[0]
    max_time = arr[-1] 
    if target_dt < min_time or target_dt > max_time:
        return -1
    idx = np.where(arr == target_dt)[0]
    return idx[0] if len(idx) > 0 else -1

def simulate_trade_sl_only(pair, df_candle, sl_percent):
    """REALISTIC SL-only simulation with proper trading logic"""
    entryIdx = find_candle_idx(pair['entryDt'], df_candle)
    exitIdx = find_candle_idx(pair['exitDt'], df_candle)
    
    # DEBUG: Check if trade dates are being found properly
    if pair['num'] <= 3:  # Debug first 3 trades
        print(f"🔍 SIMULATE DEBUG Trade {pair['num']}:")
        print(f"   Entry time: {pair['entryDt']}, found idx: {entryIdx}")
        print(f"   Exit time: {pair['exitDt']}, found idx: {exitIdx}")
        print(f"   Side: {pair['side']}, SL: {sl_percent}%")
    
    if entryIdx == -1 or exitIdx == -1 or exitIdx <= entryIdx:
        if pair['num'] <= 3:
            print(f"   ❌ Invalid indices, returning None")
        return None

    prices = df_candle.iloc[entryIdx:exitIdx+1]
    side = pair['side']
    
    # SIMPLIFIED APPROACH: For baseline (SL=0), use original prices
    # For SL testing, use realistic simulation
    if sl_percent == 0:
        # BASELINE: Use original trade prices for accuracy
        entryPrice = float(pair['entryPrice'])
        finalExitPrice = float(pair['exitPrice'])
        exitType = 'Original'
        
        if pair['num'] <= 3:
            print(f"   📊 BASELINE MODE: Using original prices")
            print(f"   Entry: {entryPrice:.8f}, Exit: {finalExitPrice:.8f}")
    else:
        # SL SIMULATION: Use ORIGINAL trade prices for accuracy, then apply SL logic
        entryPrice = float(pair['entryPrice'])  # ← FIX: Use original entry price
        originalExitPrice = float(pair['exitPrice'])  # ← FIX: Use original exit price  
        exitType = 'Signal'
        finalExitPrice = originalExitPrice
        
        # SL Logic - REALISTIC
        if side == 'LONG':
            slPrice = entryPrice * (1 - sl_percent/100)
        else:  # SHORT
            slPrice = entryPrice * (1 + sl_percent/100)
        
        # Scan through candles to check SL hit
        for i in range(len(prices)):
            high = float(prices.iloc[i]['high'])
            low = float(prices.iloc[i]['low'])
            
            if side == 'LONG' and low <= slPrice:
                finalExitPrice = max(slPrice * 0.999, low)
                exitType = 'SL'
                break
            elif side == 'SHORT' and high >= slPrice:
                finalExitPrice = min(slPrice * 1.001, high)
                exitType = 'SL'
                break
        
        if pair['num'] <= 3:
            print(f"   � SL SIMULATION MODE")
            print(f"   Entry: {entryPrice:.8f}, Exit: {finalExitPrice:.8f}")
            print(f"   SL Price: {slPrice:.8f}, Exit Type: {exitType}")
    
    # Calculate PnL with proper precision
    try:
        if side == 'LONG':
            pnlPct = (finalExitPrice - entryPrice) / entryPrice * 100.0
        else:  # SHORT
            pnlPct = (entryPrice - finalExitPrice) / entryPrice * 100.0
        
        # DEBUG: PnL calculation details
        if pair['num'] <= 3:
            print(f"   � PnL CALCULATION:")
            print(f"   Side: {side}")
            if side == 'LONG':
                print(f"   Formula: ({finalExitPrice} - {entryPrice}) / {entryPrice} * 100")
            else:
                print(f"   Formula: ({entryPrice} - {finalExitPrice}) / {entryPrice} * 100")
            print(f"   Result: {pnlPct:.4f}%")
        
        # Ensure finite values
        if not np.isfinite(pnlPct):
            print(f"⚠️ WARNING: Non-finite PnL for trade {pair['num']}: {pnlPct}")
            pnlPct = 0.0
            
    except (ZeroDivisionError, OverflowError) as e:
        print(f"⚠️ ERROR calculating PnL for trade {pair['num']}: {e}")
        pnlPct = 0.0
    
    return {
        'num': pair['num'],
        'side': side,
        'entryPrice': entryPrice,
        'exitPrice': finalExitPrice,
        'exitType': exitType,
        'pnlPct': float(pnlPct),
        'pnlPctOrigin': float(pnlPct),
        'entryDt': pair['entryDt'],
        'exitDt': pair['exitDt'],
        'sl': sl_percent,
        'be': 0,
        'ts_trig': 0,
        'ts_step': 0
    }

def calculate_advanced_metrics(details):
    """Tính toán các chỉ số nâng cao từ danh sách trade details"""
    if not details:
        return {
            'max_drawdown': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'sharpe_ratio': 0,
            'recovery_factor': 0
        }
    
    # DEBUG: Log first calculation to see actual data
    if len(details) > 0:
        print(f"🔍 ADVANCED METRICS DEBUG:")
        print(f"   Details count: {len(details)}")
        print(f"   Sample detail: {details[0] if details else 'None'}")
        if len(details) > 0 and 'pnlPct' in details[0]:
            sample_pnls = [d['pnlPct'] for d in details[:5]]
            print(f"   Sample PnLs: {sample_pnls}")
    
    # Sort theo thời gian (with fallback for sorting issues)
    try:
        sorted_details = sorted(details, key=lambda x: x['entryDt'])
    except (TypeError, KeyError) as e:
        print(f"⚠️ Sorting error: {e}, using original order")
        sorted_details = details
    
    pnl_list = [trade['pnlPct'] for trade in sorted_details]
    
    # DEBUG: Check if all PnLs are zero
    non_zero_pnls = [pnl for pnl in pnl_list if pnl != 0]
    print(f"🔍 PnL DEBUG: Total={len(pnl_list)}, Non-zero={len(non_zero_pnls)}")
    if len(non_zero_pnls) > 0:
        print(f"   Sample non-zero PnLs: {non_zero_pnls[:5]}")
    else:
        print(f"   ⚠️ ALL PnLs are ZERO! This is the problem!")
        print(f"   Sample zero PnLs: {pnl_list[:5]}")
    
    # If all PnLs are zero, return early to avoid division by zero
    if all(pnl == 0 for pnl in pnl_list):
        print(f"⚠️ All PnLs are zero, returning zero metrics")
        return {
            'max_drawdown': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'sharpe_ratio': 0,
            'recovery_factor': 0
        }
    
    # Tính Max Drawdown
    cumulative_pnl = []
    running_total = 0
    for pnl in pnl_list:
        running_total += pnl
        cumulative_pnl.append(running_total)
    
    max_drawdown = 0
    peak = cumulative_pnl[0] if cumulative_pnl else 0
    for value in cumulative_pnl:
        if value > peak:
            peak = value
        drawdown = peak - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Phân loại thắng/thua
    win_amounts = [pnl for pnl in pnl_list if pnl > 0]
    loss_amounts = [pnl for pnl in pnl_list if pnl <= 0]
    
    avg_win = sum(win_amounts) / len(win_amounts) if win_amounts else 0
    avg_loss = sum(loss_amounts) / len(loss_amounts) if loss_amounts else 0
    
    # Tính Consecutive Wins/Losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_win_streak = 0
    current_loss_streak = 0
    
    for pnl in pnl_list:
        if pnl > 0:
            current_win_streak += 1
            current_loss_streak = 0
            max_consecutive_wins = max(max_consecutive_wins, current_win_streak)
        else:
            current_loss_streak += 1
            current_win_streak = 0
            max_consecutive_losses = max(max_consecutive_losses, current_loss_streak)
    
    # Tính Sharpe Ratio
    avg_trade = sum(pnl_list) / len(pnl_list)
    if len(pnl_list) > 1:
        std_dev = math.sqrt(sum([(x - avg_trade) ** 2 for x in pnl_list]) / (len(pnl_list) - 1))
        sharpe_ratio = avg_trade / std_dev if std_dev > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Tính Recovery Factor
    total_pnl = sum(pnl_list)
    recovery_factor = total_pnl / max_drawdown if max_drawdown > 0 else float('inf') if total_pnl > 0 else 0
    
    # DEBUG: Log calculated results
    if len(details) > 0:
        print(f"🔍 ADVANCED METRICS RESULTS:")
        print(f"   PnL list length: {len(pnl_list)}")
        print(f"   Max drawdown: {max_drawdown}")
        print(f"   Avg win: {avg_win}")
        print(f"   Avg loss: {avg_loss}")
        print(f"   Max consecutive wins: {max_consecutive_wins}")
        print(f"   Max consecutive losses: {max_consecutive_losses}")
        print(f"   Sharpe ratio: {sharpe_ratio}")
        print(f"   Recovery factor: {recovery_factor}")
        print(f"   Win amounts count: {len(win_amounts)}")
        print(f"   Loss amounts count: {len(loss_amounts)}")
    
    return {
        'max_drawdown': max_drawdown,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_consecutive_wins': max_consecutive_wins,
        'max_consecutive_losses': max_consecutive_losses,
        'sharpe_ratio': safe_float(sharpe_ratio),
        'recovery_factor': safe_float(recovery_factor)
    }

def grid_search_sl_fallback(pairs, df_candle, sl_min, sl_max, sl_step, opt_type, 
                           be_min=0.5, ts_trig_min=0.5, ts_step_min=0.5):
    """Tìm kiếm lưới đơn giản không sử dụng đa luồng cho chế độ dự phòng"""
    global optimization_status
    
    print(f"🚀 TÌM KIẾM LƯỚI SL DỰ PHÒNG BẮT ĐẦU!")
    print(f"🚀 Tham số: cặp={len(pairs)}, sl_min={sl_min}, sl_max={sl_max}, sl_step={sl_step}")
    print(f"🚀 BE/TS mặc định: be_min={be_min}, ts_trig_min={ts_trig_min}, ts_step_min={ts_step_min}")
    
    results = []
    sl_list = list(np.arange(sl_min, sl_max + sl_step/2, sl_step))
    
    total_combinations = len(sl_list)
    print(f"🔄 Chế độ dự phong: Thử nghiệm {total_combinations} tổ hợp SL...")
    
    for i, sl in enumerate(sl_list):
        print(f"Tiến độ: {i+1}/{total_combinations} - Thử nghiệm SL: {sl:.1f}%")
        
        # Cập nhật tiến độ cho giao diện web
        optimization_status['current_progress'] = i + 1
        
        details = []
        win_count = 0
        gain_sum = 0
        loss_sum = 0
        
        for pair in pairs:
            res = simulate_trade_sl_only(pair, df_candle, sl)
            if res is not None:
                details.append(res)
                pnl = res['pnlPct']
                if pnl > 0: 
                    win_count += 1
                    gain_sum += pnl
                else: 
                    loss_sum += abs(pnl)  # Use abs() to get positive loss amount
        
        total_trades = len(details)
        winrate = (win_count / total_trades * 100) if total_trades > 0 else 0
        pf = (gain_sum / loss_sum) if loss_sum > 0 else float('inf') if gain_sum > 0 else 0
        pnl_total = sum([x['pnlPct'] for x in details])
        
        # Debug first SL to verify calculations
        if i == 0:
            print(f"🔍 FALLBACK DEBUG SL={sl:.1f}%:")
            print(f"   Total trades: {total_trades}")
            print(f"   Win trades: {win_count}")
            print(f"   Gain sum: {gain_sum:.4f}%")
            print(f"   Loss sum: {loss_sum:.4f}%") 
            print(f"   PnL total: {pnl_total:.4f}%")
            print(f"   Winrate: {winrate:.2f}%")
            print(f"   PF: {pf:.4f}")
            print(f"   Details structure: {details[0] if details else 'No details'}")
            
            # 🚨 CRITICAL DEBUG: Check if we have ANY non-zero PnLs
            non_zero_details = [d for d in details if d['pnlPct'] != 0]
            print(f"   🔍 CRITICAL: Non-zero PnLs count: {len(non_zero_details)}/{len(details)}")
            if len(non_zero_details) > 0:
                print(f"   Sample non-zero: {non_zero_details[0]['pnlPct']:.4f}%")
            else:
                print(f"   ⚠️ ALL PnLs ARE ZERO - THIS IS THE ROOT CAUSE!")
                
            # Also check trade pairs data
            print(f"   📊 TRADE PAIRS DEBUG:")
            print(f"   Pairs count: {len(pairs)}")
            if len(pairs) > 0:
                sample_pair = pairs[0]
                print(f"   Sample pair: num={sample_pair['num']}, side={sample_pair['side']}")
                print(f"   Entry: {sample_pair['entryPrice']}, Exit: {sample_pair['exitPrice']}")
                print(f"   Entry time: {sample_pair['entryDt']}")
                print(f"   Exit time: {sample_pair['exitDt']}")
        
        # Tính các chỉ số nâng cao
        advanced_metrics = calculate_advanced_metrics(details)
        
        # 🛡️ SAFETY CHECK: Ensure advanced_metrics has all required keys
        if not advanced_metrics or not isinstance(advanced_metrics, dict):
            print(f"⚠️ WARNING: calculate_advanced_metrics returned invalid result: {advanced_metrics}")
            advanced_metrics = {
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'sharpe_ratio': 0,
                'recovery_factor': 0
            }
        
        # 🔍 IMMEDIATE DEBUG: Log raw advanced_metrics values
        print(f"🔍 RAW ADVANCED METRICS for SL={sl:.1f}%:")
        for key, value in advanced_metrics.items():
            print(f"   {key}: {value} (type: {type(value)})")
        
        # Ensure all required keys exist
        required_keys = ['max_drawdown', 'avg_win', 'avg_loss', 'max_consecutive_wins', 'max_consecutive_losses', 'sharpe_ratio', 'recovery_factor']
        for key in required_keys:
            if key not in advanced_metrics:
                print(f"⚠️ WARNING: Missing key '{key}' in advanced_metrics, setting to 0")
                advanced_metrics[key] = 0
        
        # 🔍 DEBUG: Show safe_float conversions
        print(f"🔍 SAFE_FLOAT CONVERSIONS:")
        print(f"   max_drawdown: {advanced_metrics['max_drawdown']} -> {safe_float(advanced_metrics['max_drawdown'])}")
        print(f"   avg_win: {advanced_metrics['avg_win']} -> {safe_float(advanced_metrics['avg_win'])}")
        print(f"   sharpe_ratio: {advanced_metrics['sharpe_ratio']} -> {safe_float(advanced_metrics['sharpe_ratio'])}")
        
        # 🔍 CRITICAL DEBUG: Test what actually gets stored in results
        result_dict = {
            'sl': float(sl),
            'be': float(be_min),           # ← Use actual value instead of 0.0
            'ts_trig': float(ts_trig_min), # ← Use actual value instead of 0.0  
            'ts_step': float(ts_step_min), # ← Use actual value instead of 0.0
            'pnl_total': float(pnl_total),
            'winrate': float(winrate),
            'pf': safe_float(pf),
            'max_drawdown': safe_float(advanced_metrics['max_drawdown']),
            'avg_win': safe_float(advanced_metrics['avg_win']),
            'avg_loss': safe_float(advanced_metrics['avg_loss']),
            'max_consecutive_wins': safe_int(advanced_metrics['max_consecutive_wins']),
            'max_consecutive_losses': safe_int(advanced_metrics['max_consecutive_losses']),
            'sharpe_ratio': safe_float(advanced_metrics['sharpe_ratio']),
            'recovery_factor': safe_float(advanced_metrics['recovery_factor']),
            'details': details
        }
        
        print(f"🔍 RESULT DICT BEFORE APPEND:")
        print(f"   max_drawdown: {result_dict['max_drawdown']} (type: {type(result_dict['max_drawdown'])})")
        print(f"   avg_win: {result_dict['avg_win']} (type: {type(result_dict['avg_win'])})")
        print(f"   sharpe_ratio: {result_dict['sharpe_ratio']} (type: {type(result_dict['sharpe_ratio'])})")
        
        results.append(result_dict)
    
    # Sort by optimization type
    if opt_type == 'pnl':
        results.sort(key=lambda x: x['pnl_total'], reverse=True)
    elif opt_type == 'winrate':
        results.sort(key=lambda x: x['winrate'], reverse=True)
    elif opt_type == 'pf':
        results.sort(key=lambda x: x['pf'], reverse=True)
    elif opt_type == 'sharpe':
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
    elif opt_type == 'recovery':
        results.sort(key=lambda x: x['recovery_factor'], reverse=True)
    elif opt_type == 'drawdown':
        results.sort(key=lambda x: x['max_drawdown'], reverse=False)  # Drawdown thấp hơn là tốt hơn
    else:  # default to pnl
        results.sort(key=lambda x: x['pnl_total'], reverse=True)
    
    print(f"🔍 FALLBACK RESULTS: Top result has PnL={results[0]['pnl_total']:.4f}%, Winrate={results[0]['winrate']:.2f}%")
    
    return results

def grid_search_realistic_full(pairs, df_candle, sl_list, be_list, ts_trig_list, ts_step_list, opt_type):
    """
    TÌM KIẾM LƯỚI TOÀN DIỆN với mô phỏng đầy đủ SL + BE + TS
    Hàm này đảm bảo MÔ PHỎNG GIAO DỊCH THỰC TẾ cho tất cả tổ hợp tham số
    """
    global optimization_status
    
    print(f"🚀 TÌM KIẾM LƯỚI THỰC TẾ TOÀN DIỆN BẮT ĐẦU!")
    print(f"📊 CHẾ ĐỘ MÔ PHỎNG: SL + Breakeven + Trailing Stop đầy đủ")
    print(f"🔢 Tham số: SL={len(sl_list)}, BE={len(be_list)}, TS_TRIG={len(ts_trig_list)}, TS_STEP={len(ts_step_list)}")
    
    results = []
    total_combinations = len(sl_list) * len(be_list) * len(ts_trig_list) * len(ts_step_list)
    combination_count = 0
    
    print(f"🔄 CHẾ ĐỘ THỰC TẾ: Thử nghiệm {total_combinations:,} tổ hợp tham số...")
    print(f"💡 Mỗi lệnh sẽ được mô phỏng với:")
    print(f"   - Stop Loss: Bảo vệ vốn động")
    print(f"   - Breakeven: Di chuyển SL về hòa vốn khi đạt mục tiêu lợi nhuận")  
    print(f"   - Trailing Stop: Bảo vệ lợi nhuận động với tiến trình từng bước")
    
    for sl in sl_list:
        for be in be_list:
            for ts_trig in ts_trig_list:
                for ts_step in ts_step_list:
                    combination_count += 1
                    
                    # Cập nhật tiến độ cho giao diện web
                    optimization_status['current_progress'] = combination_count
                    
                    if combination_count % 100 == 0 or combination_count <= 10:
                        print(f"Tiến độ: {combination_count}/{total_combinations} - Thử nghiệm SL:{sl:.1f}% BE:{be:.1f}% TS:{ts_trig:.1f}%/{ts_step:.1f}%")
                    
                    # Simulate all trades with current parameter set
                    details = []
                    win_count = 0
                    gain_sum = 0
                    loss_sum = 0
                    
                    for pair in pairs:
                        # Sử dụng hàm simulate_trade NÂNG CAO với logic BE+TS đầy đủ
                        if ADVANCED_MODE:
                            result, log = simulate_trade(pair, df_candle, sl, be, ts_trig, ts_step)
                        else:
                            # Dự phòng mô phỏng chỉ SL  
                            result = simulate_trade_sl_only(pair, df_candle, sl)
                            result.update({'be': be, 'ts_trig': ts_trig, 'ts_step': ts_step})
                        
                        if result is not None:
                            details.append(result)
                            pnl = result['pnlPct']
                            if pnl > 0: 
                                win_count += 1
                                gain_sum += pnl
                            else: 
                                loss_sum += abs(pnl)
                    
                    # Tính toán các chỉ số hiệu suất
                    total_trades = len(details)
                    winrate = (win_count / total_trades * 100) if total_trades > 0 else 0
                    pf = (gain_sum / loss_sum) if loss_sum > 0 else float('inf') if gain_sum > 0 else 0
                    pnl_total = sum([x['pnlPct'] for x in details])
                    
                    # Tính toán chỉ số nâng cao sử dụng kết quả thực tế
                    advanced_metrics = calculate_advanced_metrics(details)
                    
                    # Debug vài tổ hợp đầu để xác minh mô phỏng thực tế
                    if combination_count <= 3:
                        print(f"🔍 DEBUG THỰC TẾ Tổ hợp #{combination_count}:")
                        print(f"   SL={sl:.1f}% BE={be:.1f}% TS_TRIG={ts_trig:.1f}% TS_STEP={ts_step:.1f}%")
                        print(f"   Tổng lệnh: {total_trades}")
                        print(f"   Lệnh thắng: {win_count}")
                        print(f"   Tổng PnL: {pnl_total:.4f}%")
                        print(f"   Tỷ lệ thắng: {winrate:.2f}%")
                        print(f"   Chỉ số nâng cao: Max DD={advanced_metrics['max_drawdown']:.4f}%, Sharpe={advanced_metrics['sharpe_ratio']:.4f}")
                        if len(details) > 0:
                            sample_detail = details[0]
                            print(f"   Lệnh mẫu: #{sample_detail['num']} {sample_detail['side']} -> {sample_detail['exitType']} -> {sample_detail['pnlPct']:.4f}%")
                    
                    # Store result with full parameter set
                    result_dict = {
                        'sl': float(sl),
                        'be': float(be),
                        'ts_trig': float(ts_trig),
                        'ts_step': float(ts_step),
                        'pnl_total': float(pnl_total),
                        'winrate': float(winrate),
                        'pf': safe_float(pf),
                        'max_drawdown': safe_float(advanced_metrics['max_drawdown']),
                        'avg_win': safe_float(advanced_metrics['avg_win']),
                        'avg_loss': safe_float(advanced_metrics['avg_loss']),
                        'max_consecutive_wins': safe_int(advanced_metrics['max_consecutive_wins']),
                        'max_consecutive_losses': safe_int(advanced_metrics['max_consecutive_losses']),
                        'sharpe_ratio': safe_float(advanced_metrics['sharpe_ratio']),
                        'recovery_factor': safe_float(advanced_metrics['recovery_factor']),
                        'details': details
                    }
                    
                    results.append(result_dict)
    
    # Sort by optimization type
    if opt_type == 'pnl':
        results.sort(key=lambda x: x['pnl_total'], reverse=True)
    elif opt_type == 'winrate':
        results.sort(key=lambda x: x['winrate'], reverse=True)
    elif opt_type == 'pf':
        results.sort(key=lambda x: x['pf'], reverse=True)
    elif opt_type == 'sharpe':
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
    elif opt_type == 'recovery':
        results.sort(key=lambda x: x['recovery_factor'], reverse=True)
    elif opt_type == 'drawdown':
        results.sort(key=lambda x: x['max_drawdown'], reverse=False)
    else:
        results.sort(key=lambda x: x['pnl_total'], reverse=True)
    
    print(f"🔍 KẾT QUẢ THỰC TẾ: Kết quả tốt nhất -> SL:{results[0]['sl']:.1f}% BE:{results[0]['be']:.1f}% TS:{results[0]['ts_trig']:.1f}%/{results[0]['ts_step']:.1f}%")
    print(f"   Hiệu suất: PnL={results[0]['pnl_total']:.4f}% Tỷ lệ thắng={results[0]['winrate']:.2f}% Sharpe={results[0]['sharpe_ratio']:.4f}")
    
    return results
    """Simple grid search without multiprocessing for fallback"""
    print(f"🚀 GRID_SEARCH_SL_FALLBACK STARTED!")
    print(f"🚀 Parameters: pairs={len(pairs)}, sl_min={sl_min}, sl_max={sl_max}, sl_step={sl_step}")
    print(f"🚀 BE/TS defaults: be_min={be_min}, ts_trig_min={ts_trig_min}, ts_step_min={ts_step_min}")
    
    results = []
    sl_list = list(np.arange(sl_min, sl_max + sl_step/2, sl_step))
    
    total_combinations = len(sl_list)
    print(f"🔄 Fallback mode: Testing {total_combinations} SL combinations...")
    
    for i, sl in enumerate(sl_list):
        print(f"Progress: {i+1}/{total_combinations} - Testing SL: {sl:.1f}%")
        
        # Update progress for web interface
        optimization_status['current_progress'] = i + 1
        
        details = []
        win_count = 0
        gain_sum = 0
        loss_sum = 0
        
        for pair in pairs:
            res = simulate_trade_sl_only(pair, df_candle, sl)
            if res is not None:
                details.append(res)
                pnl = res['pnlPct']
                if pnl > 0: 
                    win_count += 1
                    gain_sum += pnl
                else: 
                    loss_sum += abs(pnl)  # Use abs() to get positive loss amount
        
        total_trades = len(details)
        winrate = (win_count / total_trades * 100) if total_trades > 0 else 0
        pf = (gain_sum / loss_sum) if loss_sum > 0 else float('inf') if gain_sum > 0 else 0
        pnl_total = sum([x['pnlPct'] for x in details])
        
        # Debug first SL to verify calculations
        if i == 0:
            print(f"🔍 FALLBACK DEBUG SL={sl:.1f}%:")
            print(f"   Total trades: {total_trades}")
            print(f"   Win trades: {win_count}")
            print(f"   Gain sum: {gain_sum:.4f}%")
            print(f"   Loss sum: {loss_sum:.4f}%") 
            print(f"   PnL total: {pnl_total:.4f}%")
            print(f"   Winrate: {winrate:.2f}%")
            print(f"   PF: {pf:.4f}")
            print(f"   Details structure: {details[0] if details else 'No details'}")
            
            # 🚨 CRITICAL DEBUG: Check if we have ANY non-zero PnLs
            non_zero_details = [d for d in details if d['pnlPct'] != 0]
            print(f"   🔍 CRITICAL: Non-zero PnLs count: {len(non_zero_details)}/{len(details)}")
            if len(non_zero_details) > 0:
                print(f"   Sample non-zero: {non_zero_details[0]['pnlPct']:.4f}%")
            else:
                print(f"   ⚠️ ALL PnLs ARE ZERO - THIS IS THE ROOT CAUSE!")
                
            # Also check trade pairs data
            print(f"   📊 TRADE PAIRS DEBUG:")
            print(f"   Pairs count: {len(pairs)}")
            if len(pairs) > 0:
                sample_pair = pairs[0]
                print(f"   Sample pair: num={sample_pair['num']}, side={sample_pair['side']}")
                print(f"   Entry: {sample_pair['entryPrice']}, Exit: {sample_pair['exitPrice']}")
                print(f"   Entry time: {sample_pair['entryDt']}")
                print(f"   Exit time: {sample_pair['exitDt']}")
        
        # Tính các chỉ số nâng cao
        advanced_metrics = calculate_advanced_metrics(details)
        
        # 🛡️ SAFETY CHECK: Ensure advanced_metrics has all required keys
        if not advanced_metrics or not isinstance(advanced_metrics, dict):
            print(f"⚠️ WARNING: calculate_advanced_metrics returned invalid result: {advanced_metrics}")
            advanced_metrics = {
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'sharpe_ratio': 0,
                'recovery_factor': 0
            }
        
        # 🔍 IMMEDIATE DEBUG: Log raw advanced_metrics values
        print(f"🔍 RAW ADVANCED METRICS for SL={sl:.1f}%:")
        for key, value in advanced_metrics.items():
            print(f"   {key}: {value} (type: {type(value)})")
        
        # Ensure all required keys exist
        required_keys = ['max_drawdown', 'avg_win', 'avg_loss', 'max_consecutive_wins', 'max_consecutive_losses', 'sharpe_ratio', 'recovery_factor']
        for key in required_keys:
            if key not in advanced_metrics:
                print(f"⚠️ WARNING: Missing key '{key}' in advanced_metrics, setting to 0")
                advanced_metrics[key] = 0
        
        # 🔍 DEBUG: Show safe_float conversions
        print(f"🔍 SAFE_FLOAT CONVERSIONS:")
        print(f"   max_drawdown: {advanced_metrics['max_drawdown']} -> {safe_float(advanced_metrics['max_drawdown'])}")
        print(f"   avg_win: {advanced_metrics['avg_win']} -> {safe_float(advanced_metrics['avg_win'])}")
        print(f"   sharpe_ratio: {advanced_metrics['sharpe_ratio']} -> {safe_float(advanced_metrics['sharpe_ratio'])}")
        
        # 🔍 CRITICAL DEBUG: Test what actually gets stored in results
        result_dict = {
            'sl': float(sl),
            'be': float(be_min),           # ← Use actual value instead of 0.0
            'ts_trig': float(ts_trig_min), # ← Use actual value instead of 0.0  
            'ts_step': float(ts_step_min), # ← Use actual value instead of 0.0
            'pnl_total': float(pnl_total),
            'winrate': float(winrate),
            'pf': safe_float(pf),
            'max_drawdown': safe_float(advanced_metrics['max_drawdown']),
            'avg_win': safe_float(advanced_metrics['avg_win']),
            'avg_loss': safe_float(advanced_metrics['avg_loss']),
            'max_consecutive_wins': safe_int(advanced_metrics['max_consecutive_wins']),
            'max_consecutive_losses': safe_int(advanced_metrics['max_consecutive_losses']),
            'sharpe_ratio': safe_float(advanced_metrics['sharpe_ratio']),
            'recovery_factor': safe_float(advanced_metrics['recovery_factor']),
            'details': details
        }
        
        print(f"🔍 RESULT DICT BEFORE APPEND:")
        print(f"   max_drawdown: {result_dict['max_drawdown']} (type: {type(result_dict['max_drawdown'])})")
        print(f"   avg_win: {result_dict['avg_win']} (type: {type(result_dict['avg_win'])})")
        print(f"   sharpe_ratio: {result_dict['sharpe_ratio']} (type: {type(result_dict['sharpe_ratio'])})")
        
        results.append(result_dict)
    
    # Sort by optimization type
    if opt_type == 'pnl':
        results.sort(key=lambda x: x['pnl_total'], reverse=True)
    elif opt_type == 'winrate':
        results.sort(key=lambda x: x['winrate'], reverse=True)
    elif opt_type == 'pf':
        results.sort(key=lambda x: x['pf'], reverse=True)
    elif opt_type == 'sharpe':
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
    elif opt_type == 'recovery':
        results.sort(key=lambda x: x['recovery_factor'], reverse=True)
    elif opt_type == 'drawdown':
        results.sort(key=lambda x: x['max_drawdown'], reverse=False)  # Drawdown thấp hơn là tốt hơn
    else:  # default to pnl
        results.sort(key=lambda x: x['pnl_total'], reverse=True)
    
    print(f"🔍 FALLBACK RESULTS: Top result has PnL={results[0]['pnl_total']:.4f}%, Winrate={results[0]['winrate']:.2f}%")
    
    return results

@app.route('/')
def index():
    return render_template('index_enhanced.html')

@app.route('/classic')
def classic():
    return render_template('index.html')

@app.route('/quick_summary', methods=['POST'])
def quick_summary():
    try:
        print("=== ENHANCED QUICK SUMMARY START ===")
        
        # Lấy dữ liệu từ form
        trade_file = request.files.get('trade_file')
        candle_file = request.files.get('candle_file')
        
        if not trade_file or not candle_file:
            return jsonify({'success': False, 'error': 'Missing files'})
        
        print(f"Files: {trade_file.filename}, {candle_file.filename}")
        
        # Đọc files trực tiếp không qua tempfile để tránh treo
        trade_content = trade_file.read().decode('utf-8')
        candle_content = candle_file.read().decode('utf-8')
        
        print(f"Content lengths: Trade={len(trade_content)}, Candle={len(candle_content)}")
        
        # Load và process data - chỉ dùng content-based functions
        df_trade = load_trade_csv_from_content(trade_content)
        df_candle = load_candle_csv_from_content(candle_content)
        
        print(f"Data loaded: Trade={len(df_trade)}, Candle={len(df_candle)}")
        
        # Enhanced validation and info for user
        unique_trades = len(df_trade['trade'].unique()) if 'trade' in df_trade.columns else 0
        print(f"Trade validation: {len(df_trade)} records from {unique_trades} unique trades")
        
        # Sample price detection for format info
        if 'price' in df_trade.columns:
            sample_prices = df_trade['price'].head(10).mean()
            if sample_prices < 0.1:
                format_info = "BOME format detected (low price range)"
            elif sample_prices > 1000:
                format_info = "BTC format detected (high price range)"
            else:
                format_info = "ACE/mid-range format detected"
            print(f"Format info: {format_info}")
        
        # Filter data theo thời gian với debug
        min_candle = df_candle['time'].min()
        max_candle = df_candle['time'].max()
        print(f"🕐 SUMMARY DEBUG: Candle time range: {min_candle} to {max_candle}")
        
        min_trade = df_trade['date'].min()
        max_trade = df_trade['date'].max()
        print(f"🕐 SUMMARY DEBUG: Trade time range: {min_trade} to {max_trade}")
        
        df_trade_filtered = df_trade[(df_trade['date'] >= min_candle) & (df_trade['date'] <= max_candle)]
        print(f"🕐 SUMMARY DEBUG: Trades after time filter: {len(df_trade_filtered)} (original: {len(df_trade)})")
        
        # Lấy trade pairs - chỉ dùng local function
        trade_pairs, log_init = get_trade_pairs(df_trade_filtered)
        
        # Tính toán hiệu suất gốc bằng 2 cách để so sánh
        # Cách 1: Direct calculation từ trade pairs
        performance_direct = calculate_original_performance(trade_pairs)
        
        # Cách 2: Simulation-based calculation để so sánh
        performance_simulated = None
        simulated_details = []
        try:
            for pair in trade_pairs[:10]:  # Test với 10 lệnh đầu để không chậm
                if ADVANCED_MODE:
                    result, log = simulate_trade(pair, df_candle, 0, 0, 0, 0)
                    if result is not None:
                        simulated_details.append(result)
                else:
                    res = simulate_trade_sl_only(pair, df_candle, 0)
                    if res is not None:
                        simulated_details.append(res)
            
            if simulated_details:
                sim_pnl_total = sum([x['pnlPct'] for x in simulated_details])
                sim_winrate = len([x for x in simulated_details if x['pnlPct'] > 0]) / len(simulated_details) * 100
                performance_simulated = {
                    'total_pnl': sim_pnl_total,
                    'winrate': sim_winrate,
                    'trade_count': len(simulated_details)
                }
                print(f"🔍 COMPARISON: Direct vs Simulated PnL for first 10 trades")
                print(f"   Direct method: {performance_direct['total_pnl']/len(trade_pairs)*10:.4f}% (10 trades)")
                print(f"   Simulated method: {sim_pnl_total:.4f}% (10 trades)")
                
        except Exception as e:
            print(f"Warning: Could not run simulation comparison: {e}")
        
        # Use direct calculation as primary result
        performance = performance_direct
        
        print(f"Trade pairs: {len(trade_pairs)}")
        
        # Thông tin về candle data
        candle_count = len(df_candle)
        date_range = f"{min_candle.strftime('%m/%d %H:%M')} - {max_candle.strftime('%m/%d %H:%M')}"
        
        summary_data = {
            'success': True,
            'summary': {
                'total_trades': len(df_trade),
                'valid_trades': len(trade_pairs),
                'candle_count': candle_count,
                'date_range': date_range,
                'total_pnl': performance['total_pnl'] if performance else 0,
                'winrate': performance['winrate'] if performance else 0,
                'profit_factor': performance['profit_factor'] if performance else 0,
                'avg_trade': performance['avg_trade'] if performance else 0,
                'win_trades': performance['win_trades'] if performance else 0,
                'loss_trades': performance['loss_trades'] if performance else 0,
                'max_drawdown': performance['max_drawdown'] if performance else 0,
                'avg_win': performance['avg_win'] if performance else 0,
                'avg_loss': performance['avg_loss'] if performance else 0,
                'max_consecutive_wins': performance['max_consecutive_wins'] if performance else 0,
                'max_consecutive_losses': performance['max_consecutive_losses'] if performance else 0,
                'sharpe_ratio': performance['sharpe_ratio'] if performance else 0,
                'recovery_factor': performance['recovery_factor'] if performance else 0
            },
            'comparison': {
                'direct_method': performance_direct['total_pnl'] if performance_direct else 0,
                'simulated_method': performance_simulated['total_pnl'] if performance_simulated else 'N/A',
                'method_note': 'Direct = từ trade pairs, Simulated = qua engine mô phỏng'
            } if performance_simulated else None
        }
        
        print("=== ENHANCED QUICK SUMMARY SUCCESS ===")
        return jsonify(convert_to_serializable(summary_data))
        
    except Exception as e:
        print(f"=== ENHANCED QUICK SUMMARY ERROR: {str(e)} ===")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/suggest_parameters', methods=['POST'])
def suggest_parameters():
    """Smart parameter range suggestion based on tradelist analysis"""
    try:
        print("=== SMART PARAMETER SUGGESTION START ===")
        
        # Get files from request
        trade_file = request.files.get('trade_file')
        
        if not trade_file:
            return jsonify({'success': False, 'error': 'Missing trade file for analysis'})
        
        print(f"Analyzing tradelist: {trade_file.filename}")
        
        # Read and process trade data
        trade_content = trade_file.read().decode('utf-8')
        print(f"Trade content length: {len(trade_content)} chars")
        
        # Load trade data
        df_trade = load_trade_csv_from_content(trade_content)
        print(f"Loaded {len(df_trade)} trade records")
        
        # Extract trade pairs for analysis
        trade_pairs, log_init = get_trade_pairs(df_trade)
        print(f"Extracted {len(trade_pairs)} valid trade pairs")
        
        # Check minimum data requirement
        if len(trade_pairs) < 10:
            return jsonify({
                'success': False, 
                'error': f'Không đủ dữ liệu để phân tích thông minh. Cần ít nhất 10 trades, hiện tại chỉ có {len(trade_pairs)} trades.'
            })
        
        # Import and run Smart Range Finder
        try:
            import tempfile
            import os
            
            # Create temporary tradelist file for analysis
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as temp_file:
                temp_file.write(trade_content)
                temp_path = temp_file.name
            
            try:
                # Import Smart Range Finder classes
                from smart_range_finder import SmartRangeFinder
                from dynamic_step_calculator import DynamicStepCalculator
                
                print("🔍 Running Smart Range Finder analysis...")
                
                # Initialize and run Smart Range Finder
                finder = SmartRangeFinder(temp_path)
                analysis_results = finder.analyze_price_movement_patterns()
                recommendations = finder.generate_final_recommendations()
                
                print("🔍 Running Dynamic Step Calculator...")
                
                # Initialize and run Dynamic Step Calculator
                calculator = DynamicStepCalculator(temp_path)
                step_report = calculator.generate_comprehensive_report()
                
                # Extract parameter ranges from balanced strategy
                param_ranges = recommendations['parameter_ranges']
                step_data = step_report['parameter_steps']
                
                # Build response with statistical foundation
                suggested_params = {
                    'sl_min': param_ranges['sl']['min'],
                    'sl_max': param_ranges['sl']['max'],
                    'sl_step': step_data['sl_steps']['balanced'],
                    
                    'be_min': param_ranges['be']['min'], 
                    'be_max': param_ranges['be']['max'],
                    'be_step': step_data['be_steps']['balanced'],
                    
                    'ts_trig_min': param_ranges['ts_trigger']['min'],
                    'ts_trig_max': param_ranges['ts_trigger']['max'], 
                    'ts_trig_step': step_data['ts_trigger_steps']['balanced'],
                    
                    'ts_step_min': param_ranges['ts_step']['min'],
                    'ts_step_max': param_ranges['ts_step']['max'],
                    'ts_step_step': step_data['ts_step_steps']['balanced']
                }
                
                # Calculate efficiency gains
                efficiency_gain = recommendations['efficiency_gain']
                combinations_count = recommendations['combinations_count']
                
                # Build explanation
                explanation = {
                    'data_analysis': f"Phân tích {len(trade_pairs)} trades với {recommendations['total_trades_analyzed']} exit records",
                    'strategy_selected': f"Chiến lược Balanced được chọn tự động (cân bằng rủi ro/lợi nhuận)",
                    'statistical_foundation': [
                        f"SL Range: {param_ranges['sl']['min']:.1f}%-{param_ranges['sl']['max']:.1f}% dựa trên phân tích drawdown patterns",
                        f"BE Range: {param_ranges['be']['min']:.2f}%-{param_ranges['be']['max']:.2f}% dựa trên early run-up patterns", 
                        f"TS Trigger: {param_ranges['ts_trigger']['min']:.2f}%-{param_ranges['ts_trigger']['max']:.2f}% dựa trên profit development patterns",
                        f"TS Step: {param_ranges['ts_step']['min']:.2f}%-{param_ranges['ts_step']['max']:.2f}% dựa trên volatility adjustment"
                    ],
                    'step_logic': [
                        f"SL Step ({step_data['sl_steps']['balanced']}): {step_data['sl_steps']['base_calculation']}",
                        f"BE Step ({step_data['be_steps']['balanced']}): {step_data['be_steps']['base_calculation']}",
                        f"TS Trigger Step ({step_data['ts_trigger_steps']['balanced']}): {step_data['ts_trigger_steps']['base_calculation']}",
                        f"TS Step Step ({step_data['ts_step_steps']['balanced']}): {step_data['ts_step_steps']['base_calculation']}"
                    ]
                }
                
                response_data = {
                    'success': True,
                    'suggested_parameters': suggested_params,
                    'explanation': explanation,
                    'efficiency': {
                        'efficiency_gain': efficiency_gain,
                        'smart_combinations': combinations_count,
                        'estimated_time_savings': f"{efficiency_gain:.1f}x faster than blind search"
                    },
                    'data_quality': {
                        'total_trades_analyzed': len(trade_pairs),
                        'data_quality_issues': recommendations.get('data_quality_issues', [])
                    }
                }
                
                print(f"✅ Smart parameter suggestion complete!")
                print(f"   SL: {suggested_params['sl_min']:.1f}%-{suggested_params['sl_max']:.1f}% (step: {suggested_params['sl_step']})")
                print(f"   BE: {suggested_params['be_min']:.2f}%-{suggested_params['be_max']:.2f}% (step: {suggested_params['be_step']})")
                print(f"   Efficiency: {efficiency_gain:.1f}x improvement")
                
                return jsonify(convert_to_serializable(response_data))
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except ImportError as e:
            print(f"⚠️ Smart Range Finder not available: {e}")
            return jsonify({
                'success': False,
                'error': 'Smart Range Finder module không có sẵn. Vui lòng kiểm tra smart_range_finder.py và dynamic_step_calculator.py files.'
            })
        
    except Exception as e:
        print(f"=== SMART PARAMETER SUGGESTION ERROR: {str(e)} ===")
        return jsonify({'success': False, 'error': f'Lỗi phân tích thông số: {str(e)}'})

@app.route('/optimize', methods=['POST'])
def optimize():
    global optimization_status
    try:
        print("🚨🚨🚨 OPTIMIZE ROUTE HIT! 🚨🚨🚨")
        print("=== ENHANCED OPTIMIZATION START ===")
        
        # Lấy dữ liệu từ form
        trade_file = request.files['trade_file']
        candle_file = request.files['candle_file']
        
        # 🚨 DEBUG: Print raw form data to see what browser is actually sending
        print(f"🔍 RAW FORM DATA DEBUG:")
        for key, value in request.form.items():
            print(f"   {key} = '{value}'")
        
        # Parameters cơ bản
        sl_min = float(request.form['sl_min'])
        sl_max = float(request.form['sl_max'])
        sl_step = float(request.form['sl_step'])
        
        # Parameters BE (Breakeven) - Fixed defaults to match HTML + robust parsing
        be_min = safe_float_parse(request.form, 'be_min', 0.5)  # Handle empty strings
        be_max = safe_float_parse(request.form, 'be_max', 2.0)  # Handle empty strings
        be_step = safe_float_parse(request.form, 'be_step', 0.5)
        
        # Parameters TS (Trailing Stop) - Fixed defaults to match HTML + robust parsing
        ts_trig_min = safe_float_parse(request.form, 'ts_trig_min', 0.5)  # Handle empty strings
        ts_trig_max = safe_float_parse(request.form, 'ts_trig_max', 3.0)  # Handle empty strings
        ts_trig_step = safe_float_parse(request.form, 'ts_trig_step', 0.5)
        
        ts_step_min = safe_float_parse(request.form, 'ts_step_min', 0.5)  # Handle empty strings
        ts_step_max = safe_float_parse(request.form, 'ts_step_max', 1.0)  # Handle empty strings
        ts_step_step = safe_float_parse(request.form, 'ts_step_step', 0.2)
        
        # 🔍 DEBUG: Print exactly what server received
        print(f"🔍 SERVER RECEIVED PARAMETERS:")
        print(f"   SL: min={sl_min}, max={sl_max}, step={sl_step}")
        print(f"   BE: min={be_min}, max={be_max}, step={be_step}")
        print(f"   TS_TRIG: min={ts_trig_min}, max={ts_trig_max}, step={ts_trig_step}")
        print(f"   TS_STEP: min={ts_step_min}, max={ts_step_max}, step={ts_step_step}")
        
        # Trade selection parameters  
        max_trades = int(request.form.get('max_trades', 0))
        start_trade = int(request.form.get('start_trade', 1))
        selection_mode = request.form.get('trade_selection_mode', 'sequence')
        
        opt_type = request.form['opt_type']
        
        print(f"Enhanced Parameters: SL {sl_min}-{sl_max}, BE {be_min}-{be_max}, TS {ts_trig_min}-{ts_trig_max}/{ts_step_min}-{ts_step_max}, opt={opt_type}")
        
        # Đọc files trực tiếp để tránh treo
        trade_content = trade_file.read().decode('utf-8')
        candle_content = candle_file.read().decode('utf-8')
        
        print(f"Files loaded: Trade={len(trade_content)} chars, Candle={len(candle_content)} chars")
        
        # Load và process data - ưu tiên content-based để tránh treo
        try:
            df_trade = load_trade_csv_from_content(trade_content)
            df_candle = load_candle_csv_from_content(candle_content)
            print("Using content-based loading (safer)")
        except Exception as content_error:
            print(f"Content loading failed: {content_error}")
            # Fallback to file-based nếu cần
            try:
                # Tạo temp files
                trade_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
                candle_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
                
                trade_temp.write(trade_content)
                candle_temp.write(candle_content)
                trade_temp.close()
                candle_temp.close()
                
                # Load using file-based functions
                df_trade = load_trade_csv_file(trade_temp.name)
                df_candle = load_candle_csv_file(candle_temp.name)
                
                # Clean up temp files
                os.unlink(trade_temp.name)
                os.unlink(candle_temp.name)
                print("Using file-based loading (fallback)")
                
            except Exception as file_error:
                print(f"File loading also failed: {file_error}")
                raise content_error
        
        # Filter data theo thời gian
        min_candle = df_candle['time'].min()
        max_candle = df_candle['time'].max()
        print(f"🕐 DEBUG: Candle time range: {min_candle} to {max_candle}")
        
        min_trade = df_trade['date'].min()
        max_trade = df_trade['date'].max()
        print(f"🕐 DEBUG: Trade time range: {min_trade} to {max_trade}")
        
        df_trade = df_trade[(df_trade['date'] >= min_candle) & (df_trade['date'] <= max_candle)]
        print(f"🕐 DEBUG: Trades after time filter: {len(df_trade)} (original: {len(df_trade) + len(df_trade[(df_trade['date'] < min_candle) | (df_trade['date'] > max_candle)])})")
        
        if len(df_trade) == 0:
            return jsonify({'error': f'Không có trade nào nằm trong khoảng thời gian của dữ liệu nến! Candle: {min_candle} to {max_candle}, Trade: {min_trade} to {max_trade}. Hint: Kiểm tra xem bạn có upload đúng cặp file trade/candle không (VD: BOME trade với BOME candle, BTC trade với BTC candle)'})
        
        # Lấy trade pairs - ưu tiên local function
        try:
            trade_pairs, log_init = get_trade_pairs(df_trade)
            print("Using content-based trade pairs")
        except Exception:
            try:
                trade_pairs, log_init = get_trade_pairs_file(df_trade)
                print("Using file-based trade pairs")
            except Exception as e:
                return jsonify({'error': f'Lỗi xử lý trade pairs: {str(e)}'})
        
        if len(trade_pairs) == 0:
            return jsonify({'error': 'Không có trade pairs hợp lệ!'})
        
        # Filter trades theo tham số người dùng
        original_count = len(trade_pairs)
        trade_pairs = filter_trades_by_selection(trade_pairs, max_trades, start_trade, selection_mode)
        filtered_count = len(trade_pairs)
        
        if len(trade_pairs) == 0:
            return jsonify({'error': f'Không có trade nào sau khi lọc! (Gốc: {original_count} lệnh)'})
        
        # Log thông tin lọc
        filter_info = f"Enhanced: Đã lọc từ {original_count} xuống {filtered_count} lệnh"
        if max_trades > 0:
            filter_info += f" (tối đa {max_trades})"
        if start_trade < 0:
            filter_info += f" (từ {abs(start_trade)} lệnh cuối)"
        elif start_trade > 1:
            filter_info += f" (từ lệnh #{start_trade})"
        filter_info += f" (chế độ: {selection_mode})"
        
        print(filter_info)
        
        # Tạo parameter lists - FIX: Handle min=max cases properly
        sl_list = list(np.arange(sl_min, sl_max + sl_step/2, sl_step))
        
        # BE parameters: If min=max=0, use [0]. If min=max>0, use [min]. If min<max, use range.
        if be_min == be_max == 0:
            be_list = [0]
        elif be_min == be_max:
            be_list = [be_min]  # Single value case (e.g., min=max=0.5)
        else:
            be_list = list(np.arange(be_min, be_max + be_step/2, be_step))
            
        # TS Trigger parameters: Same logic as BE
        if ts_trig_min == ts_trig_max == 0:
            ts_trig_list = [0]
        elif ts_trig_min == ts_trig_max:
            ts_trig_list = [ts_trig_min]  # Single value case
        else:
            ts_trig_list = list(np.arange(ts_trig_min, ts_trig_max + ts_trig_step/2, ts_trig_step))
            
        # TS Step parameters: Same logic as BE
        if ts_step_min == ts_step_max == 0:
            ts_step_list = [0]
        elif ts_step_min == ts_step_max:
            ts_step_list = [ts_step_min]  # Single value case
        else:
            ts_step_list = list(np.arange(ts_step_min, ts_step_max + ts_step_step/2, ts_step_step))
        
        # Debug: Print parameter lists
        print(f"🔍 PARAMETER LISTS DEBUG:")
        print(f"   SL: {sl_list}")
        print(f"   BE: {be_list}")
        print(f"   TS_TRIG: {ts_trig_list}")
        print(f"   TS_STEP: {ts_step_list}")
        
        total_combinations = len(sl_list) * len(be_list) * len(ts_trig_list) * len(ts_step_list)
        print(f"Total combinations to test: {total_combinations}")
        
        # Cho phép user override limit nếu muốn test nhiều combinations
        force_advanced = request.form.get('force_advanced_mode', 'false').lower() == 'true'
        combinations_limit = 1000000 if force_advanced else 100000  # Nâng limit cao hơn nhiều
        
        # 🔍 DEBUG MODE SELECTION
        print(f"🔍 MODE SELECTION DEBUG:")
        print(f"   ADVANCED_MODE = {ADVANCED_MODE}")
        print(f"   total_combinations = {total_combinations}")
        print(f"   force_advanced = {force_advanced}")
        print(f"   combinations_limit = {combinations_limit:,}")
        print(f"   Condition (ADVANCED_MODE and total_combinations <= {combinations_limit}): {ADVANCED_MODE and total_combinations <= combinations_limit}")
        
        # Chạy grid search với nhận diện chế độ
        if ADVANCED_MODE and total_combinations <= combinations_limit:  # Giới hạn có thể điều chỉnh
            print("🚀 SỬ DỤNG CHẾ ĐỘ NÂNG CAO với tối ưu SL+BE+TS đầy đủ")
            print("🔥 MÔ PHỎNG THỰC TẾ: Mỗi lệnh sẽ được kiểm tra với logic BE và TS động")
            if total_combinations > 10000:
                print(f"🚨 CẢNH BÁO: Thử nghiệm {total_combinations:,} tổ hợp - Có thể mất 10+ phút!")
            elif total_combinations > 1000:
                print(f"🚨 CẢNH BÁO: Thử nghiệm {total_combinations:,} tổ hợp - Có thể mất vài phút!")
            
            # Cập nhật theo dõi tiến độ
            optimization_status.update({
                'running': True,
                'start_time': datetime.now(),
                'total_combinations': total_combinations,
                'current_progress': 0,
                'status_message': f'Tối ưu thực tế nâng cao: {total_combinations:,} tổ hợp'
            })
            
            # 🚀 QUAN TRỌNG: Sử dụng mô phỏng thực tế đầy đủ của chúng ta thay vì grid_search_parallel có thể bị lỗi
            print(f"🔍 GỌI grid_search_realistic_full với {len(trade_pairs)} cặp...")
            print(f"   Điều này đảm bảo MÔ PHỎNG BE + TS ĐÚNG ĐẮN cho tất cả {total_combinations:,} tổ hợp")
            results = grid_search_realistic_full(trade_pairs, df_candle, sl_list, be_list, ts_trig_list, ts_step_list, opt_type)
            print(f"🔍 grid_search_realistic_full trả về {len(results)} kết quả")
            
            # 🔍 DEBUG: Kiểm tra xem kết quả có chỉ số nâng cao không
            if results and len(results) > 0:
                sample_result = results[0]
                print(f"🔍 CÁC KEY KẾT QUẢ MẪU: {list(sample_result.keys())}")
                print(f"🔍 KẾT QUẢ TỐT NHẤT: SL={sample_result['sl']:.1f}% BE={sample_result['be']:.1f}% TS={sample_result['ts_trig']:.1f}%/{sample_result['ts_step']:.1f}%")
                print(f"   Hiệu suất: PnL={sample_result['pnl_total']:.4f}% Sharpe={sample_result.get('sharpe_ratio', 'THIẾU')}")
            
            # Xác minh chỉ số nâng cao có mặt
            advanced_keys = ['max_drawdown', 'avg_win', 'avg_loss', 'sharpe_ratio', 'recovery_factor', 'max_consecutive_wins', 'max_consecutive_losses']
            missing_keys = [key for key in advanced_keys if key not in results[0]]
            if missing_keys:
                print(f"⚠️ CẢNH BÁO: Thiếu các key nâng cao trong kết quả: {missing_keys}")
                # 🛡️ AN TOÀN: Thêm chỉ số nâng cao thiếu nếu grid_search_parallel không cung cấp
                print("🛠️ AN TOÀN: Thêm chỉ số nâng cao thiếu...")
                for result in results:
                    if not all(key in result for key in advanced_keys):
                        advanced_metrics = calculate_advanced_metrics(result['details'])
                        for key in advanced_keys:
                            if key not in result:
                                result[key] = safe_float(advanced_metrics[key])
                                print(f"   Đã thêm {key}: {result[key]}")
            else:
                print("✅ Tất cả chỉ số nâng cao có mặt trong kết quả")
                has_advanced = all(key in sample_result for key in ['max_drawdown', 'avg_win', 'avg_loss', 'sharpe_ratio', 'recovery_factor'])
                print(f"🔍 HAS ADVANCED METRICS: {has_advanced}")
                
                if not has_advanced:
                    print("⚠️ WARNING: Results missing advanced metrics! Adding fallback calculation...")
                    # Add advanced metrics to existing results
                    for result in results:
                        if 'details' in result and result['details']:
                            advanced_metrics = calculate_advanced_metrics(result['details'])
                            result.update({
                                'max_drawdown': safe_float(advanced_metrics['max_drawdown']),
                                'avg_win': safe_float(advanced_metrics['avg_win']),
                                'avg_loss': safe_float(advanced_metrics['avg_loss']),
                                'max_consecutive_wins': safe_int(advanced_metrics['max_consecutive_wins']),
                                'max_consecutive_losses': safe_int(advanced_metrics['max_consecutive_losses']),
                                'sharpe_ratio': safe_float(advanced_metrics['sharpe_ratio']),
                                'recovery_factor': safe_float(advanced_metrics['recovery_factor'])
                            })
                    print(f"✅ Added advanced metrics to {len(results)} results")
            
            # 🛡️ SAFETY CHECK: If advanced mode returns empty results, fall back to SL-only mode
            if not results or len(results) == 0:
                print("⚠️ CẢNH BÁO: Chế độ nâng cao trả về kết quả trống! Chuyển sang tối ưu chỉ SL...")
                print("⚠️ Thông thường điều này có nghĩa là module mô phỏng nâng cao không thể tải đúng cách")
                
                # Fall back to SL-only optimization
                results = grid_search_sl_fallback(trade_pairs, df_candle, sl_min, sl_max, sl_step, opt_type,
                                                be_min, ts_trig_min, ts_step_min)
                
                print(f"✅ Dự phòng hoàn tất: Tạo ra {len(results)} kết quả chỉ SL với chỉ số nâng cao")
            
            # Mark optimization as complete
            optimization_status.update({
                'running': False,
                'status_message': f'Hoàn tất: Tạo ra {len(results)} kết quả'
            })
            
            # Convert results để JSON serializable
            for result in results:
                result['sl'] = float(result['sl'])
                result['be'] = float(result['be'])
                result['ts_trig'] = float(result['ts_trig'])
                result['ts_step'] = float(result['ts_step'])
                result['pnl_total'] = float(result['pnl_total'])
                result['winrate'] = float(result['winrate'])
                result['pf'] = float(result['pf'])
                
                # Clean details
                for detail in result['details']:
                    detail['num'] = safe_int(detail['num'])
                    detail['entryPrice'] = float(detail['entryPrice'])
                    detail['exitPrice'] = float(detail['exitPrice'])
                    detail['pnlPct'] = float(detail['pnlPct'])
                    detail['pnlPctOrigin'] = float(detail['pnlPctOrigin'])
        else:
            # Fallback mode - chỉ SL để tránh treo với nhiều combinations
            print(f"🚨 WARNING: Using FALLBACK MODE - SL optimization only (combinations: {total_combinations})")
            print(f"🚨 BE/TS parameters will NOT be optimized, only displayed as input values!")
            print(f"🚨 To enable full optimization, reduce parameter ranges to ≤1000 combinations")
            
            # Update progress tracking for fallback mode
            optimization_status.update({
                'running': True,
                'start_time': datetime.now(),
                'total_combinations': len(sl_list),  # Only SL combinations in fallback
                'current_progress': 0,
                'status_message': f'Fallback mode: {len(sl_list)} SL values (BE/TS fixed)'
            })
            
            results = grid_search_sl_fallback(trade_pairs, df_candle, sl_min, sl_max, sl_step, opt_type,
                                            be_min, ts_trig_min, ts_step_min)
            
            # Mark fallback optimization as complete
            optimization_status.update({
                'running': False,
                'status_message': f'Fallback completed: {len(results)} SL-only results'
            })
        
        # Tính baseline với enhanced error handling và debug
        baseline_details = []
        baseline_logs = []
        baseline_debug_count = 0
        
        print(f"🔍 BASELINE DEBUG: Processing {len(trade_pairs)} trade pairs...")
        
        for pair in trade_pairs:
            try:
                if ADVANCED_MODE:
                    result, log = simulate_trade(pair, df_candle, 0, 0, 0, 0)  # No optimization
                    if result is not None:
                        # Convert để đảm bảo JSON serializable
                        result_clean = {
                            'num': safe_int(result['num']),
                            'side': str(result['side']),
                            'entryPrice': float(result['entryPrice']),
                            'exitPrice': float(result['exitPrice']),
                            'exitType': str(result['exitType']),
                            'pnlPct': float(result['pnlPct']),
                            'pnlPctOrigin': float(result['pnlPctOrigin']),
                            'entryDt': result['entryDt'],
                            'exitDt': result['exitDt'],
                            'sl': 0.0,
                            'be': 0.0,
                            'ts_trig': 0.0,
                            'ts_step': 0.0
                        }
                        baseline_details.append(result_clean)
                        baseline_logs.extend(log)
                else:
                    # Use simulation engine for baseline calculation (no SL/BE/TS)
                    # This ensures same calculation method as optimization results
                    res = simulate_trade_sl_only(pair, df_candle, 0)  # No SL = baseline
                    if res is not None:
                        baseline_details.append(res)
                        
                        # Debug first few trades to verify calculation
                        if baseline_debug_count < 5:
                            print(f"🔍 BASELINE Trade {res['num']}: Entry={res['entryPrice']:.8f}, Exit={res['exitPrice']:.8f}, Side={res['side']}, PnL={res['pnlPct']:.4f}%")
                            
                            # Also show manual calculation for comparison
                            if res['side'] == 'LONG':
                                manual_pnl = (res['exitPrice'] - res['entryPrice']) / res['entryPrice'] * 100
                            else:
                                manual_pnl = (res['entryPrice'] - res['exitPrice']) / res['entryPrice'] * 100
                            print(f"🔍 MANUAL Trade {res['num']}: Manual PnL={manual_pnl:.4f}%, Simulated PnL={res['pnlPct']:.4f}%")
                            baseline_debug_count += 1
                            
            except Exception as e:
                print(f"Warning: Error processing baseline for trade {pair['num']}: {str(e)}")
                continue
        
        print(f"🔍 BASELINE DEBUG: Generated {len(baseline_details)} baseline results")
        
        # CRITICAL FIX: Calculate baseline stats from ORIGINAL trade pairs instead of simulation
        # This ensures baseline comparison uses real tradelist data
        original_baseline_pnl = 0
        original_baseline_wins = 0
        
        for pair in trade_pairs:
            if pair['side'] == 'LONG':
                pnl_pct = (pair['exitPrice'] - pair['entryPrice']) / pair['entryPrice'] * 100
            else:  # SHORT
                pnl_pct = (pair['entryPrice'] - pair['exitPrice']) / pair['entryPrice'] * 100
            
            original_baseline_pnl += pnl_pct
            if pnl_pct > 0:
                original_baseline_wins += 1
        
        baseline_winrate = (original_baseline_wins / len(trade_pairs) * 100) if trade_pairs else 0
        baseline_pnl = original_baseline_pnl
        
        print(f"🔍 BASELINE CORRECTED: Using ORIGINAL data - PnL={baseline_pnl:.4f}%, Winrate={baseline_winrate:.2f}%")
        
        # Format kết quả
        best_result = results[0] if results else None
        
        # 🚨 DEBUG: Check best_result structure and advanced metrics values
        if best_result:
            print(f"🔍 BEST RESULT DEBUG (BEFORE CONVERSION):")
            print(f"   PnL Total: {best_result.get('pnl_total', 'MISSING')}")
            print(f"   Max Drawdown: {best_result.get('max_drawdown', 'MISSING')}")
            print(f"   Avg Win: {best_result.get('avg_win', 'MISSING')}")
            print(f"   Avg Loss: {best_result.get('avg_loss', 'MISSING')}")
            print(f"   Sharpe Ratio: {best_result.get('sharpe_ratio', 'MISSING')}")
            print(f"   Recovery Factor: {best_result.get('recovery_factor', 'MISSING')}")
            print(f"   Max Win Streak: {best_result.get('max_consecutive_wins', 'MISSING')}")
            print(f"   Max Loss Streak: {best_result.get('max_consecutive_losses', 'MISSING')}")
            
            # Check if any advanced metrics are zero
            zero_metrics = []
            for metric in ['max_drawdown', 'avg_win', 'avg_loss', 'sharpe_ratio', 'recovery_factor', 'max_consecutive_wins', 'max_consecutive_losses']:
                value = best_result.get(metric, 'MISSING')
                if value == 0 or value == 0.0:
                    zero_metrics.append(f"{metric}={value}")
            
            if zero_metrics:
                print(f"   ⚠️ ZERO METRICS DETECTED: {zero_metrics}")
            else:
                print(f"   ✅ NO ZERO METRICS IN BEST RESULT")
            print(f"   Avg Win: {best_result.get('avg_win', 'MISSING')}")
            print(f"   Avg Loss: {best_result.get('avg_loss', 'MISSING')}")
            print(f"   Sharpe Ratio: {best_result.get('sharpe_ratio', 'MISSING')}")
            print(f"   Recovery Factor: {best_result.get('recovery_factor', 'MISSING')}")
            print(f"   Max Consecutive Wins: {best_result.get('max_consecutive_wins', 'MISSING')}")
            print(f"   Max Consecutive Losses: {best_result.get('max_consecutive_losses', 'MISSING')}")
            print(f"   Available keys: {list(best_result.keys())}")
        
        # Tính cumulative PnL cho so sánh
        def calculate_cumulative_pnl(details):
            """Tính PnL tích lũy theo thời gian"""
            if not details:
                return [], []
            
            # Sort theo entry datetime để có thứ tự thời gian chính xác
            sorted_details = sorted(details, key=lambda x: x['entryDt'])
            
            cumulative_pnl = []
            current_total = 0
            trade_labels = []
            
            for i, trade in enumerate(sorted_details, 1):
                current_total += trade['pnlPct']
                cumulative_pnl.append(float(current_total))
                # Format datetime cho label
                entry_time = trade['entryDt'].strftime('%m/%d %H:%M') if hasattr(trade['entryDt'], 'strftime') else f"Trade {i}"
                trade_labels.append(entry_time)
            
            return trade_labels, cumulative_pnl
        
        # Tính cumulative cho baseline và best result
        # CRITICAL FIX: Use ORIGINAL trade pairs for baseline cumulative PnL calculation
        # instead of simulation results to ensure accuracy
        original_baseline_details = create_original_baseline_details(trade_pairs)
        baseline_labels, baseline_cumulative = calculate_cumulative_pnl(original_baseline_details)
        
        if best_result and best_result['details']:
            best_labels, best_cumulative = calculate_cumulative_pnl(best_result['details'])
        else:
            best_labels, best_cumulative = [], []
        
        # Tạo trade comparison logs cho top 50 trades gần đây nhất
        trade_comparison = []
        if best_result and best_result['details']:
            baseline_dict = {t['num']: t for t in baseline_details}
            optimized_dict = {t['num']: t for t in best_result['details']}
            
            # CRITICAL FIX: Tạo dictionary từ trade_pairs gốc để có entry/exit price thật
            original_pairs_dict = {p['num']: p for p in trade_pairs}
            
            # Lấy tất cả trade nums có trong cả baseline và optimized
            all_trade_nums = sorted(set(baseline_dict.keys()) & set(optimized_dict.keys()))
            
            # Sort theo entry time để lấy 50 lệnh gần đây nhất (mới nhất)
            trade_with_time = []
            for trade_num in all_trade_nums:
                baseline_trade = baseline_dict[trade_num]
                optimized_trade = optimized_dict[trade_num]
                improvement = optimized_trade['pnlPct'] - baseline_trade['pnlPct']
                trade_with_time.append((baseline_trade['entryDt'], trade_num, improvement))
            
            # Sort theo thời gian giảm dần (mới nhất trước) và lấy top 50
            trade_with_time.sort(key=lambda x: x[0], reverse=True)
            top_trades = [(abs(improvement), trade_num, improvement) for _, trade_num, improvement in trade_with_time[:50]]
            
            for abs_improvement, trade_num, improvement in top_trades:
                baseline_trade = baseline_dict[trade_num]
                optimized_trade = optimized_dict[trade_num]
                
                # CRITICAL FIX: Use ORIGINAL trade pair data for baseline entry/exit prices
                # because simulation might be calculating wrong baseline prices
                if trade_num in original_pairs_dict:
                    original_pair = original_pairs_dict[trade_num]
                    # Use original entry/exit prices from tradelist for baseline
                    entry_price = float(original_pair['entryPrice'])
                    baseline_exit_price = float(original_pair['exitPrice'])
                    print(f"🔍 TRADE {trade_num}: Using ORIGINAL prices - Entry={entry_price:.8f}, Exit={baseline_exit_price:.8f}")
                else:
                    # Fallback to simulation results if no original pair found
                    entry_price = float(baseline_trade['entryPrice'])
                    baseline_exit_price = float(baseline_trade['exitPrice'])
                    print(f"⚠️ TRADE {trade_num}: Using SIMULATION prices - Entry={entry_price:.8f}, Exit={baseline_exit_price:.8f}")
                
                optimized_exit_price = float(optimized_trade['exitPrice'])
                
                # Calculate baseline PnL using ORIGINAL prices from tradelist
                if trade_num in original_pairs_dict:
                    original_pair = original_pairs_dict[trade_num]
                    side = original_pair['side']
                    if side == 'LONG':
                        baseline_pnl_calculated = (baseline_exit_price - entry_price) / entry_price * 100
                    else:  # SHORT
                        baseline_pnl_calculated = (entry_price - baseline_exit_price) / entry_price * 100
                    print(f"🔍 TRADE {trade_num}: Original PnL calculation - {baseline_pnl_calculated:.4f}% vs Simulation: {baseline_trade['pnlPct']:.4f}%")
                else:
                    # Fallback to simulation PnL
                    baseline_pnl_calculated = baseline_trade['pnlPct']
                
                # Determine decimal places based on price magnitude
                if entry_price < 0.01:
                    decimal_places = 6  # Very small prices like BOME (0.009xxx)
                elif entry_price < 1:
                    decimal_places = 4  # Small prices like ACEUSDT (0.4xxx)
                else:
                    decimal_places = 2  # Normal prices like BTC (50000+)
                
                # Calculate improvement using recalculated baseline PnL
                improvement_recalc = optimized_trade['pnlPct'] - baseline_pnl_calculated
                
                trade_info = {
                    'trade_num': safe_int(trade_num),
                    'entry_time': baseline_trade['entryDt'].strftime('%m/%d %H:%M'),
                    'side': baseline_trade['side'],
                    'entry_price': round(entry_price, decimal_places),
                    'baseline_exit_price': round(baseline_exit_price, decimal_places),
                    'baseline_exit_type': 'Signal',
                    'baseline_pnl': round(float(baseline_pnl_calculated), 2),
                    'optimized_exit_price': round(optimized_exit_price, decimal_places),
                    'optimized_exit_type': optimized_trade.get('exitType', 'Signal'),
                    'optimized_pnl': round(float(optimized_trade['pnlPct']), 2),
                    'improvement': round(float(improvement_recalc), 2),
                    'price_format': f'{{:.{decimal_places}f}}'
                }
                
                # Debug first few trades
                if len(trade_comparison) < 5:
                    print(f"🔍 BACKEND TRADE {trade_num} DATA:")
                    print(f"   Entry Price: {trade_info['entry_price']}")
                    print(f"   Baseline Exit Price: {trade_info['baseline_exit_price']}")
                    print(f"   Original entry from pair: {entry_price:.8f}")
                    print(f"   Original exit from pair: {baseline_exit_price:.8f}")
                
                trade_comparison.append(trade_info)
        
        response_data = {
            'success': True,
            'filter_info': filter_info,
            'mode': 'ADVANCED' if (ADVANCED_MODE and total_combinations <= combinations_limit) else 'FALLBACK',
            'mode_details': {
                'advanced_mode_available': ADVANCED_MODE,
                'total_combinations': total_combinations,
                'combinations_limit': combinations_limit,
                'fallback_reason': f'Too many combinations ({total_combinations:,} > {combinations_limit:,})' if total_combinations > combinations_limit else None,
                'optimization_scope': 'SL + BE + TS (Full Grid Search)' if (ADVANCED_MODE and total_combinations <= combinations_limit) else 'SL only (BE/TS fixed)',
                'warning': f'🚨 BE/TS parameters NOT optimized - only {len(sl_list)} SL values tested!' if total_combinations > combinations_limit else None,
                'actual_tests_run': len(sl_list) if total_combinations > combinations_limit else total_combinations
            },
            'baseline': {
                'pnl_total': float(baseline_pnl),
                'winrate': float(baseline_winrate),
                'trade_count': int(len(baseline_details))
            },
            'best_result': {
                'sl': float(best_result['sl']),
                'be': float(best_result['be']),
                'ts_trig': float(best_result['ts_trig']),
                'ts_step': float(best_result['ts_step']),
                'pnl_total': float(best_result['pnl_total']),
                'winrate': float(best_result['winrate']),
                'pf': safe_float(best_result['pf']),
                'max_drawdown': best_result.get('max_drawdown', 0.0),
                'avg_win': best_result.get('avg_win', 0.0),
                'avg_loss': best_result.get('avg_loss', 0.0),
                'max_consecutive_wins': best_result.get('max_consecutive_wins', 0),
                'max_consecutive_losses': best_result.get('max_consecutive_losses', 0),
                'sharpe_ratio': best_result.get('sharpe_ratio', 0.0),
                'recovery_factor': best_result.get('recovery_factor', 0.0),
                'trade_win': int(len([d for d in best_result['details'] if d['pnlPct'] > 0])),
                'trade_loss': int(len([d for d in best_result['details'] if d['pnlPct'] <= 0]))
            } if best_result else None,
            'all_results': convert_to_serializable(results[:20]),
            'cumulative_comparison': {
                'labels': baseline_labels,
                'baseline_cumulative': baseline_cumulative,
                'optimized_cumulative': best_cumulative,
                'baseline_label': 'Kết quả gốc (No Optimization)',
                'optimized_label': f'Enhanced Tối ưu (SL:{best_result["sl"]:.1f}% BE:{best_result["be"]:.1f}% TS:{best_result["ts_trig"]:.1f}%/{best_result["ts_step"]:.1f}%)' if best_result else 'N/A'
            },
            'trade_comparison': trade_comparison,
            'total_combinations': len(results)
        }
        
        # 🔍 FINAL DEBUG: Log what's actually being sent to frontend
        if best_result:
            response_best = response_data['best_result']
            print(f"🔍 FINAL API RESPONSE DEBUG:")
            print(f"   Max Drawdown: {response_best['max_drawdown']} (best_result has: {best_result.get('max_drawdown', 'MISSING')})")
            print(f"   Avg Win: {response_best['avg_win']} (best_result has: {best_result.get('avg_win', 'MISSING')})")
            print(f"   Avg Loss: {response_best['avg_loss']} (best_result has: {best_result.get('avg_loss', 'MISSING')})")
            print(f"   Sharpe Ratio: {response_best['sharpe_ratio']} (best_result has: {best_result.get('sharpe_ratio', 'MISSING')})")
            print(f"   Recovery Factor: {response_best['recovery_factor']} (best_result has: {best_result.get('recovery_factor', 'MISSING')})")
            print(f"   Max Win Streak: {response_best['max_consecutive_wins']} (best_result has: {best_result.get('max_consecutive_wins', 'MISSING')})")
            print(f"   Max Loss Streak: {response_best['max_consecutive_losses']} (best_result has: {best_result.get('max_consecutive_losses', 'MISSING')})")
        
        print("=== ENHANCED OPTIMIZATION SUCCESS ===")
        return jsonify(response_data)
        
    except Exception as e:
        # Reset optimization status on error
        optimization_status.update({
            'running': False,
            'status_message': f'Error: {str(e)}'
        })
        
        print(f"=== ENHANCED OPTIMIZATION ERROR: {str(e)} ===")
        print(traceback.format_exc())
        return jsonify({'error': str(e)})

@app.route('/progress', methods=['GET'])
def get_progress():
    """Get current optimization progress"""
    global optimization_status
    
    if optimization_status['running']:
        elapsed = datetime.now() - optimization_status['start_time'] if optimization_status['start_time'] else timedelta(0)
        elapsed_minutes = elapsed.total_seconds() / 60
        
        # Calculate estimated completion if we have progress
        if optimization_status['current_progress'] > 0 and optimization_status['total_combinations'] > 0:
            progress_ratio = optimization_status['current_progress'] / optimization_status['total_combinations']
            if progress_ratio > 0:
                total_estimated_minutes = elapsed_minutes / progress_ratio
                remaining_minutes = total_estimated_minutes - elapsed_minutes
                eta = datetime.now() + timedelta(minutes=remaining_minutes)
                optimization_status['estimated_completion'] = eta.strftime('%H:%M:%S')
        
        return jsonify({
            'running': True,
            'progress_percent': round((optimization_status['current_progress'] / optimization_status['total_combinations']) * 100, 2) if optimization_status['total_combinations'] > 0 else 0,
            'current_combination': optimization_status['current_progress'],
            'total_combinations': optimization_status['total_combinations'],
            'elapsed_time': f"{elapsed_minutes:.1f} minutes",
            'estimated_completion': optimization_status.get('estimated_completion', 'Calculating...'),
            'status_message': optimization_status['status_message']
        })
    else:
        return jsonify({
            'running': False,
            'status_message': optimization_status['status_message']
        })

@app.route('/status')
def status():
    """Simple status page to monitor optimization"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Optimization Progress Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #ffffff; }
            .container { max-width: 800px; margin: 0 auto; }
            .status-card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 10px 0; }
            .progress-bar { width: 100%; background: #444; height: 20px; border-radius: 10px; overflow: hidden; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A); transition: width 0.3s; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0; }
            .metric { background: #333; padding: 15px; border-radius: 5px; text-align: center; }
            .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
            .metric-label { font-size: 12px; color: #ccc; margin-top: 5px; }
            .refresh-btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .refresh-btn:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Trading Optimization Progress Monitor</h1>
            
            <div class="status-card">
                <h2>Current Status</h2>
                <div id="status-message">Loading...</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
                </div>
                <div id="progress-text">0%</div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value" id="current-combination">-</div>
                    <div class="metric-label">Current Combination</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="total-combinations">-</div>
                    <div class="metric-label">Total Combinations</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="elapsed-time">-</div>
                    <div class="metric-label">Elapsed Time</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="eta">-</div>
                    <div class="metric-label">ETA</div>
                </div>
            </div>
            
            <button class="refresh-btn" onclick="updateProgress()">🔄 Refresh Now</button>
            <button class="refresh-btn" onclick="toggleAutoRefresh()">⏸️ Toggle Auto-refresh</button>
            <div style="margin-top: 10px; font-size: 12px; color: #888;">
                Auto-refresh: <span id="auto-refresh-status">ON</span> | Last update: <span id="last-update">-</span>
            </div>
        </div>
        
        <script>
            let autoRefresh = true;
            let refreshInterval;
            
            function updateProgress() {
                fetch('/progress')
                    .then(response => response.json())
                    .then(data => {
                        if (data.running) {
                            document.getElementById('status-message').innerHTML = 
                                `🔄 <strong>OPTIMIZATION RUNNING</strong><br>${data.status_message}`;
                            document.getElementById('progress-fill').style.width = data.progress_percent + '%';
                            document.getElementById('progress-text').textContent = data.progress_percent + '%';
                            document.getElementById('current-combination').textContent = data.current_combination.toLocaleString();
                            document.getElementById('total-combinations').textContent = data.total_combinations.toLocaleString();
                            document.getElementById('elapsed-time').textContent = data.elapsed_time;
                            document.getElementById('eta').textContent = data.estimated_completion;
                        } else {
                            document.getElementById('status-message').innerHTML = 
                                `✅ <strong>READY</strong><br>${data.status_message}`;
                            document.getElementById('progress-fill').style.width = '0%';
                            document.getElementById('progress-text').textContent = 'Ready';
                        }
                        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    })
                    .catch(error => {
                        document.getElementById('status-message').innerHTML = 
                            `❌ <strong>ERROR</strong><br>Cannot connect to server`;
                        console.error('Error:', error);
                    });
            }
            
            function toggleAutoRefresh() {
                autoRefresh = !autoRefresh;
                document.getElementById('auto-refresh-status').textContent = autoRefresh ? 'ON' : 'OFF';
                
                if (autoRefresh) {
                    refreshInterval = setInterval(updateProgress, 2000); // Update every 2 seconds
                } else {
                    clearInterval(refreshInterval);
                }
            }
            
            // Start auto-refresh
            updateProgress();
            refreshInterval = setInterval(updateProgress, 2000);
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 Starting Enhanced Trading Optimization Web App...")
    print("📊 ACEUSDT format support: ENABLED")
    print("🔄 Legacy BTC/BOME format support: ENABLED") 
    print("🌐 Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)