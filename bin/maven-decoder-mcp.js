#!/usr/bin/env node

/**
 * Maven Decoder MCP Server - Node.js Wrapper
 * 
 * This script provides a Node.js wrapper around the Python-based Maven Decoder MCP server.
 * It automatically installs Python dependencies and starts the server.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const PYTHON_COMMANDS = ['python3', 'python'];
const PACKAGE_NAME = 'maven-decoder-mcp';
const MCP_SDK_URL = 'git+https://github.com/modelcontextprotocol/python-sdk.git';

/**
 * Check if a command exists
 */
function commandExists(command) {
    try {
        require('child_process').execSync(`which ${command}`, { stdio: 'ignore' });
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Find available Python command
 */
function findPython() {
    for (const cmd of PYTHON_COMMANDS) {
        if (commandExists(cmd)) {
            return cmd;
        }
    }
    return null;
}

/**
 * Check if package is installed
 */
function isPackageInstalled(pythonCmd) {
    try {
        require('child_process').execSync(`${pythonCmd} -c "import maven_decoder_mcp"`, { stdio: 'ignore' });
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Install Python package
 */
async function installPackage(pythonCmd) {
    console.log('📦 Installing Maven Decoder MCP...');
    
    return new Promise((resolve, reject) => {
        const install = spawn(pythonCmd, ['-m', 'pip', 'install', PACKAGE_NAME, MCP_SDK_URL], {
            stdio: 'inherit'
        });
        
        install.on('close', (code) => {
            if (code === 0) {
                console.log('✅ Installation complete!');
                resolve();
            } else {
                reject(new Error(`Installation failed with code ${code}`));
            }
        });
    });
}

/**
 * Start the MCP server
 */
async function startServer(pythonCmd) {
    console.log('🚀 Starting Maven Decoder MCP Server...');
    
    const server = spawn(pythonCmd, ['-m', 'maven_decoder_mcp.maven_decoder_server'], {
        stdio: 'inherit'
    });
    
    server.on('close', (code) => {
        console.log(`Server exited with code ${code}`);
        process.exit(code);
    });
    
    server.on('error', (error) => {
        console.error('❌ Server error:', error.message);
        process.exit(1);
    });
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\\n🛑 Shutting down server...');
        server.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
        console.log('\\n🛑 Shutting down server...');
        server.kill('SIGTERM');
    });
}

/**
 * Main function
 */
async function main() {
    console.log('Maven Decoder MCP Server (Node.js Wrapper)');
    console.log('==========================================');
    
    // Check for Python
    const pythonCmd = findPython();
    if (!pythonCmd) {
        console.error('❌ Python is required but not found.');
        console.error('   Please install Python 3.8+ and try again.');
        process.exit(1);
    }
    
    console.log(`✅ Found Python: ${pythonCmd}`);
    
    // Check if package is installed
    if (!isPackageInstalled(pythonCmd)) {
        console.log('📦 Maven Decoder MCP not found, installing...');
        try {
            await installPackage(pythonCmd);
        } catch (error) {
            console.error('❌ Installation failed:', error.message);
            console.error('   You can manually install with: pip install maven-decoder-mcp');
            process.exit(1);
        }
    } else {
        console.log('✅ Maven Decoder MCP is installed');
    }
    
    // Start server
    await startServer(pythonCmd);
}

// Run main function
if (require.main === module) {
    main().catch((error) => {
        console.error('❌ Error:', error.message);
        process.exit(1);
    });
}
