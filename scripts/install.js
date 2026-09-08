#!/usr/bin/env node

/**
 * Post-install script for Maven Decoder MCP npm package
 * This script runs after npm install to set up the Python environment
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔧 Setting up Maven Decoder MCP...');

// Check for Python
function findPython() {
    const commands = ['python3', 'python'];
    for (const cmd of commands) {
        try {
            require('child_process').execSync(`which ${cmd}`, { stdio: 'ignore' });
            return cmd;
        } catch (error) {
            continue;
        }
    }
    return null;
}

// Main setup
async function setup() {
    const pythonCmd = findPython();
    
    if (!pythonCmd) {
        console.log('⚠️  Python not found - will be installed when first run');
        console.log('   To install manually: pip install maven-decoder-mcp');
        return;
    }
    
    console.log(`✅ Found Python: ${pythonCmd}`);
    console.log('📦 Pre-installing Maven Decoder MCP for faster startup...');
    
    try {
        // The PyPI package declares the MCP SDK as a dependency already.
        const install = spawn(pythonCmd, [
            '-m', 'pip', 'install',
            'maven-decoder-mcp'
        ], {
            stdio: 'inherit'
        });
        
        await new Promise((resolve, reject) => {
            install.on('close', (code) => {
                if (code === 0) {
                    console.log('✅ Pre-installation complete!');
                    resolve();
                } else {
                    console.log(`⚠️  Pre-installation failed (code ${code}) - will retry on first run`);
                    resolve(); // Don't fail the npm install
                }
            });
        });
    } catch (error) {
        console.log('⚠️  Pre-installation failed - will retry on first run');
    }
}

if (require.main === module) {
    setup().catch(console.error);
}
