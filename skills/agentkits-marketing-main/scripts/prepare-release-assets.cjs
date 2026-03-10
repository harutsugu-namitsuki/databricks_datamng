#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Generate metadata.json aligned with the package version and
 * bundle the release archive ahead of the semantic-release publish step.
 */
(function main() {
  const version = process.argv[2];

  if (!version) {
    console.error('✗ Missing required version argument for prepare-release-assets');
    process.exit(1);
  }

  const projectRoot = process.cwd();
  const packageJsonPath = path.join(projectRoot, 'package.json');
  const claudeDir = path.join(projectRoot, '.claude');
  const metadataPath = path.join(claudeDir, 'metadata.json');
  const distDir = path.join(projectRoot, 'dist');
  const archivePath = path.join(distDir, 'agentkits-marketing.zip');

  try {
    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

    if (packageJson.version !== version) {
      console.warn(
        `⚠️ package.json version (${packageJson.version}) does not match semantic-release version (${version}).`
      );
    }

    const requiredFields = ['name', 'description', 'repository'];
    const missingFields = requiredFields.filter((field) => !packageJson[field]);

    if (missingFields.length > 0) {
      throw new Error(`Missing required fields in package.json: ${missingFields.join(', ')}`);
    }

    if (!fs.existsSync(claudeDir)) {
      fs.mkdirSync(claudeDir, { recursive: true });
    }

    const metadata = {
      version: packageJson.version,
      name: packageJson.name,
      description: packageJson.description,
      buildDate: new Date().toISOString(),
      repository: packageJson.repository,
      download: {
        lastDownloadedAt: null,
        downloadedBy: null,
        installCount: 0,
      },
    };

    fs.writeFileSync(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`, 'utf8');
    console.log(`✓ Generated metadata.json with version ${metadata.version}`);

    // Sync version into .claude-plugin/plugin.json and marketplace.json
    const pluginJsonPath = path.join(projectRoot, '.claude-plugin', 'plugin.json');
    const marketplaceJsonPath = path.join(projectRoot, '.claude-plugin', 'marketplace.json');

    if (fs.existsSync(pluginJsonPath)) {
      const pluginJson = JSON.parse(fs.readFileSync(pluginJsonPath, 'utf8'));
      pluginJson.version = version;
      fs.writeFileSync(pluginJsonPath, `${JSON.stringify(pluginJson, null, 2)}\n`, 'utf8');
      console.log(`✓ Synced plugin.json to version ${version}`);
    }

    if (fs.existsSync(marketplaceJsonPath)) {
      const marketplaceJson = JSON.parse(fs.readFileSync(marketplaceJsonPath, 'utf8'));
      if (marketplaceJson.metadata) {
        marketplaceJson.metadata.version = version;
        marketplaceJson.metadata.updatedAt = new Date().toISOString().split('T')[0];
      }
      fs.writeFileSync(marketplaceJsonPath, `${JSON.stringify(marketplaceJson, null, 2)}\n`, 'utf8');
      console.log(`✓ Synced marketplace.json to version ${version}`);
    }

    if (!fs.existsSync(distDir)) {
      fs.mkdirSync(distDir, { recursive: true });
    }

    if (fs.existsSync(archivePath)) {
      fs.unlinkSync(archivePath);
    }

    const archiveTargets = [
      '.claude-plugin',
      '.claude',
      '.opencode',
      'plans',
      '.gitignore',
      '.repomixignore',
      '.mcp.json',
      'CLAUDE.md',
    ];

    const existingTargets = archiveTargets.filter((target) => fs.existsSync(path.join(projectRoot, target)));

    if (existingTargets.length === 0) {
      throw new Error('No release assets found to include in archive.');
    }

    const zipCommand = ['zip', '-r', archivePath, ...existingTargets].join(' ');
    execSync(zipCommand, { stdio: 'inherit' });
    console.log(`✓ Prepared ${archivePath}`);
  } catch (error) {
    console.error(`✗ Failed to prepare release assets: ${error.message}`);
    process.exit(1);
  }
})();
