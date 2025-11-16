# DNS-Secure Deployment Workflow

This document describes the GitHub Actions deployment workflow for the DNS-Secure application.

## Overview

The deployment workflow (`deploy.yml`) orchestrates the deployment of the DNS-Secure application components:

1. **Data Ingestion** - ETW DNS capture tool for real-time DNS event collection
2. **Backend** - (Placeholder) Future backend API service
3. **Frontend** - (Placeholder) Future web interface

## Workflow Triggers

The workflow can be triggered in two ways:

### 1. Manual Dispatch (Workflow Dispatch)

Trigger manually from the GitHub Actions UI:

- **Environment**: Choose between `staging` or `production`
- **Skip Tests**: Option to skip integration tests

### 2. Tag Push

Automatically triggered when pushing version tags:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Workflow Jobs

### 1. Check Dependencies

**Purpose**: Determine if Python packages are already installed to avoid redundant installations.

**Steps**:
- Checks cache for previously installed dependencies
- Verifies if required packages (like pywintrace) are installed
- Outputs whether installation is needed

**Outputs**:
- `deps-cached`: Boolean indicating if dependencies are cached

### 2. Install Dependencies

**Purpose**: Install Python packages only if they're not already present.

**Condition**: Runs only if dependencies are not cached

**Steps**:
- Upgrades pip
- Installs dependencies from `requirements.txt`
- Installs testing dependencies (pytest, pytest-cov)
- Verifies installation
- Caches dependencies for future runs

### 3. Deploy Data Ingestion

**Purpose**: Deploy and validate the ETW DNS capture tool (data ingestion component).

**Steps**:
- Installs/verifies dependencies (with redundancy check)
- Verifies tool can display help
- Tests tool with fake provider
- Validates JSON output format
- Generates at least 5 test events
- Uploads test output as artifact

**Validation**:
- Tool must run without errors
- Must generate valid JSONL output
- Events must have required schema fields

### 4. Deploy Backend

**Purpose**: Placeholder for future backend service deployment.

**Current Status**: Not yet implemented - this is a placeholder step

**Future Implementation**:
- Build backend service
- Deploy to server
- Configure endpoints
- Health check

### 5. Deploy Frontend

**Purpose**: Placeholder for future web UI deployment.

**Current Status**: Not yet implemented - this is a placeholder step

**Future Implementation**:
- Build frontend assets
- Deploy to web server
- Configure API endpoints
- Verify UI accessibility

### 6. Integration Tests

**Purpose**: Run comprehensive tests after deployment.

**Condition**: Runs unless `skip_tests` is true

**Steps**:
- Runs unit test suite with coverage
- Tests CLI help command
- Tests filtering capabilities (domain filters)
- Generates integration test summary

**Test Coverage**:
- Unit tests for all components
- CLI functionality
- Filtering capabilities
- Data ingestion operations

### 7. Deployment Summary

**Purpose**: Generate final deployment report.

**Always runs** (even if previous jobs fail) to provide complete status.

**Output**:
- Environment information
- Component status for each deployment
- Overall deployment result
- Notes about placeholder components

## Usage Examples

### Deploy to Staging

1. Go to Actions tab in GitHub
2. Select "Deploy DNS-Secure App" workflow
3. Click "Run workflow"
4. Select "staging" environment
5. Click "Run workflow"

### Deploy to Production

1. Create and push a version tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

Or use manual dispatch:
1. Go to Actions tab
2. Select "Deploy DNS-Secure App" workflow
3. Click "Run workflow"
4. Select "production" environment
5. Click "Run workflow"

### Deploy Without Tests

1. Go to Actions tab
2. Select "Deploy DNS-Secure App" workflow
3. Click "Run workflow"
4. Check "Skip test execution"
5. Click "Run workflow"

## Dependency Management

The workflow intelligently handles package installation:

### First Run
- No cache exists
- All packages are installed
- Installation is cached for future runs

### Subsequent Runs (with cache)
- Cache is restored
- Dependencies are verified
- Only missing packages are installed
- Significantly faster deployment

### Cache Invalidation
- Cache key is based on `requirements.txt` hash
- Changing dependencies invalidates cache
- New dependencies are installed and cached

## Windows Runner Requirements

This workflow runs on **Windows runners** (`windows-latest`) because:

1. ETW (Event Tracing for Windows) is Windows-only
2. `pywintrace` library requires Windows
3. DNS capture tool needs Windows APIs

### System Requirements
- Windows 10/11 or Windows Server 2019+
- Python 3.10+
- Administrative privileges (for actual ETW capture, not needed for fake provider tests)

## Testing Strategy

### Fake Provider Mode
The workflow uses `--fake-provider` mode for testing:
- Generates synthetic DNS events
- Doesn't require administrative privileges
- Validates tool functionality without real ETW access
- Safe for CI/CD environment

### Test Validation
- JSON format validation
- Schema version verification
- Event count verification
- Field presence checks

## Artifacts

### Data Ingestion Test Output
- **Name**: `data-ingestion-test-output`
- **Content**: Test JSONL file with sample events
- **Retention**: 7 days
- **Purpose**: Verify deployment generated valid output

## Monitoring and Debugging

### View Workflow Runs
1. Go to Actions tab in GitHub
2. Select workflow run
3. View job logs for detailed output

### Common Issues

#### Dependencies Not Installing
- Check `requirements.txt` format
- Verify GitHub can access package sources
- Check pip cache status

#### ETW Tool Fails
- Review tool logs in job output
- Check Python version compatibility
- Verify pywintrace installation

#### Tests Failing
- Check unit test output
- Review integration test logs
- Verify fake provider mode is working

## Future Enhancements

### Backend Component
When backend is implemented:
- Add backend build steps
- Configure deployment target
- Add health check endpoints
- Integrate with data ingestion

### Frontend Component
When frontend is implemented:
- Add frontend build (npm/webpack)
- Deploy static assets
- Configure API endpoint URLs
- Add UI smoke tests

### Additional Features
- Multi-environment support (dev, staging, prod)
- Rollback capability
- Blue-green deployment
- Performance benchmarking
- Security scanning
- Automated version bumping

## Contributing

To modify the deployment workflow:

1. Edit `.github/workflows/deploy.yml`
2. Test changes in a feature branch
3. Verify workflow runs successfully
4. Submit pull request

## Support

For issues with the deployment workflow:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Open a GitHub issue with:
   - Workflow run URL
   - Error messages
   - Expected vs actual behavior
