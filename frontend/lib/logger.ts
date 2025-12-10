/**
 * Enhanced logging utility for Survey Sensei frontend
 * Provides structured, colorized, and readable console logging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'success';

interface LogStyle {
  emoji: string;
  color: string;
  bgColor?: string;
}

const LOG_STYLES: Record<LogLevel, LogStyle> = {
  debug: { emoji: '🔍', color: '#6B7280' },
  info: { emoji: 'ℹ️', color: '#3B82F6' },
  warn: { emoji: '⚠️', color: '#F59E0B' },
  error: { emoji: '❌', color: '#EF4444' },
  success: { emoji: '✅', color: '#10B981' },
};

const CATEGORY_STYLES: Record<string, LogStyle> = {
  api: { emoji: '🌐', color: '#8B5CF6' },
  state: { emoji: '📦', color: '#EC4899' },
  navigation: { emoji: '🧭', color: '#06B6D4' },
  form: { emoji: '📝', color: '#14B8A6' },
  agent: { emoji: '🤖', color: '#F97316' },
  cache: { emoji: '💾', color: '#84CC16' },
  ui: { emoji: '🎨', color: '#A855F7' },
};

class Logger {
  private isDevelopment: boolean;
  private enableColors: boolean;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
    this.enableColors = true;
  }

  /**
   * Format timestamp for logs
   */
  private getTimestamp(): string {
    const now = new Date();
    return now.toTimeString().split(' ')[0] + '.' + now.getMilliseconds().toString().padStart(3, '0');
  }

  /**
   * Core logging method
   */
  private log(
    level: LogLevel,
    message: string,
    data?: any,
    category?: string
  ): void {
    if (!this.isDevelopment && level === 'debug') {
      return; // Skip debug logs in production
    }

    const timestamp = this.getTimestamp();
    const style = LOG_STYLES[level];
    const categoryStyle = category ? CATEGORY_STYLES[category] : null;

    // Build log parts - simplified format
    const parts: string[] = [];
    const styles: string[] = [];

    // Timestamp (dimmed)
    parts.push('%c[%s]');
    styles.push('color: #9CA3AF; font-size: 11px');

    // Level emoji only (no label for cleaner output)
    parts.push(`%c${style.emoji}`);
    styles.push(`color: ${style.color}; font-weight: bold`);

    // Category emoji only if provided
    if (categoryStyle) {
      parts.push(`%c${categoryStyle.emoji}`);
      styles.push(`color: ${categoryStyle.color}`);
    }

    // Message
    parts.push('%c' + message);
    styles.push('color: inherit');

    // Construct format string
    const format = parts.join(' ');
    const args = [format, ...styles, timestamp];

    // Output log
    if (level === 'error') {
      console.error(...args);
      if (data !== undefined) {
        console.error('  └─', data);
      }
    } else if (level === 'warn') {
      console.warn(...args);
      if (data !== undefined) {
        console.warn('  └─', data);
      }
    } else {
      console.log(...args);
      // Only show data for info/debug if it's meaningful
      if (data !== undefined && level !== 'success') {
        if (typeof data === 'object' && Object.keys(data).length > 0) {
          console.log('  └─', data);
        } else if (typeof data !== 'object') {
          console.log('  └─', String(data));
        }
      }
    }
  }

  /**
   * Standard log methods
   */
  debug(message: string, data?: any, category?: string): void {
    this.log('debug', message, data, category);
  }

  info(message: string, data?: any, category?: string): void {
    this.log('info', message, data, category);
  }

  warn(message: string, data?: any, category?: string): void {
    this.log('warn', message, data, category);
  }

  error(message: string, error?: Error | any, category?: string): void {
    this.log('error', message, error, category);
    if (error?.stack) {
      console.error('  Stack:', error.stack);
    }
  }

  success(message: string, data?: any, category?: string): void {
    this.log('success', message, data, category);
  }

  /**
   * Category-specific logging methods
   */
  api(operation: string, details?: any): void {
    this.log('info', operation, details, 'api');
  }

  apiSuccess(operation: string, duration?: number): void {
    const msg = duration ? `${operation} (${duration}ms)` : operation;
    this.log('success', msg, undefined, 'api');
  }

  apiError(operation: string, error: any): void {
    this.log('error', `${operation} failed`, error, 'api');
  }

  state(action: string, data?: any): void {
    this.log('debug', action, data, 'state');
  }

  navigation(action: string, details?: any): void {
    this.log('info', action, details, 'navigation');
  }

  form(action: string, data?: any): void {
    this.log('debug', action, data, 'form');
  }

  agent(action: string, details?: any): void {
    this.log('info', action, details, 'agent');
  }

  cache(action: string, key: string, hit?: boolean): void {
    const hitStatus = hit === true ? 'HIT ✅' : hit === false ? 'MISS ❌' : '';
    this.log('debug', `${action} ${key} ${hitStatus}`, undefined, 'cache');
  }

  ui(action: string, details?: any): void {
    this.log('debug', action, details, 'ui');
  }

  /**
   * Visual separators for grouping logs
   */
  group(title: string): void {
    if (this.isDevelopment) {
      console.group(
        `%c${title}`,
        'color: #6366F1; font-weight: bold; font-size: 14px; padding: 4px 0'
      );
    }
  }

  groupEnd(): void {
    if (this.isDevelopment) {
      console.groupEnd();
    }
  }

  separator(title?: string): void {
    if (this.isDevelopment) {
      if (title) {
        console.log(
          `%c\n${'='.repeat(60)}\n  ${title}\n${'='.repeat(60)}`,
          'color: #6366F1; font-weight: bold'
        );
      } else {
        console.log(`%c${'─'.repeat(60)}`, 'color: #9CA3AF');
      }
    }
  }

  /**
   * Performance timing
   */
  time(label: string): void {
    if (this.isDevelopment) {
      console.time(`⏱️  ${label}`);
    }
  }

  timeEnd(label: string): void {
    if (this.isDevelopment) {
      console.timeEnd(`⏱️  ${label}`);
    }
  }

  /**
   * Table display for structured data
   */
  table(data: any): void {
    if (this.isDevelopment) {
      console.table(data);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export type for external use
export type { LogLevel };
