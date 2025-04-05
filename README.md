# Log_Analyzer

A real-time log analysis tool that processes log streams and provides dynamic insights with adaptive monitoring capabilities.

## Requirements Satisfied

- Compatible with log_generator.sh
- Multi-threaded architecture to handle different tasks concurrently
- Real-time log stream processing
- Live display of comprehensive log statistics
- Efficient data structures for pattern tracking and analysis
- Timestamp-based rate calculations

## Build & Run Instructions
1. Download the `log_generator.sh` script from the provided GitHub link.

2. In a Bash terminal, run the following command to start the log analyzer:
```bash
   ./log_generator.sh & tail -f test_logs.log | python log_analyzer.py
   ```

3. To stop both processes: Press Ctrl+C to exit the log analyzer

## Assumptions
- Timestamps should be gathered from the log file, not during log processing.

## Performance Characterstics and Known Limitations
- The rate struggles to keep up with 1,000 entries per second. Further testing needed to conclude the root cause. But I think it may be a rate miscalculation due to the fact that timestamps are gathered from the log_generator. 
- Unfortunately I was not able to meet all requirements during the time window.
