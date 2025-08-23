/**
 * Maven Decoder MCP Server - Node.js Module
 * 
 * This module provides Node.js integration for the Maven Decoder MCP server.
 */

const { spawn } = require('child_process');
const path = require('path');

/**
 * Maven Decoder MCP Server wrapper class
 */
class MavenDecoderMCP {
    constructor(options = {}) {
        this.pythonCmd = options.pythonCmd || 'python3';
        this.serverProcess = null;
        this.options = options;
    }
    
    /**
     * Start the MCP server
     */
    async start() {
        return new Promise((resolve, reject) => {
            this.serverProcess = spawn(this.pythonCmd, ['-m', 'maven_decoder_mcp.maven_decoder_server'], {
                stdio: this.options.stdio || 'pipe',
                env: { ...process.env, ...this.options.env }
            });
            
            this.serverProcess.on('spawn', () => {
                resolve(this.serverProcess);
            });
            
            this.serverProcess.on('error', (error) => {
                reject(error);
            });
        });
    }
    
    /**
     * Stop the MCP server
     */
    stop() {
        if (this.serverProcess) {
            this.serverProcess.kill('SIGTERM');
            this.serverProcess = null;
        }
    }
    
    /**
     * Check if server is running
     */
    isRunning() {
        return this.serverProcess && !this.serverProcess.killed;
    }
}

/**
 * Convenience function to start server
 */
function createServer(options = {}) {
    return new MavenDecoderMCP(options);
}

module.exports = {
    MavenDecoderMCP,
    createServer
};
