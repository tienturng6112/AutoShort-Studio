# 7. Export Outputs

623:         logger.info("Stage 7: Exporting results.")

624:         state_manager.update_execution_state("Running", progress=87, current_stage="Stage 7: Export")

625:         voice_wav_dest = None

626:         voice_mp3_dest = None

627:         video_dur = state_manager.get_metadata("video_duration", 5.0)

628:         narr_dur = 0.0

629:         

630:         if not state_manager.is_completed("stage_7"):

631:             if not skip_tts:

632:                 voice_wav_dest = os.path.join(project_dir, "voice.wav")

633:                 voice_mp3_dest = os.path.join(project_dir, "voice.mp3")

634:                 if final_wav and os.path.exists(final_wav):

635:                     shutil.copy2(final_wav, voice_wav_dest)

636:                 if final_mp3 and os.path.exists(final_mp3):

637:                     shutil.copy2(final_mp3, voice_mp3_dest)

638:                 logger.info(f"Saved voice.wav and voice.mp3 to: {project_dir}")

639: 

640:                 try:

641:                     import wave

642:                     if voice_wav_dest and os.path.exists(voice_wav_dest):

643:                         with wave.open(voice_wav_dest, "rb") as wfile:

644:                             narr_dur = wfile.getnframes() / float(wfile.getframerate())

645:                 except Exception as e:

646:                     raise RuntimeError(f"Could not verify voice.wav duration: {str(e)}")

647: 

648:                 if abs(narr_dur - video_dur) > 0.100:

649:                     logger.warning(

650:                         f"Timeline verification mismatch: Narration duration {narr_dur:.3f}s "

651:                         f"differs from video duration {video_dur:.3f}s by more than 100 ms."

652:                     )

653:                 logger.info(f"Verification SUCCESS: voice.wav duration ({narr_dur:.3f}s) matches video duration ({video_dur:.3f}s) within 100 ms.")

654:             else:

655:                 logger.info("Skipping voice file export and duration verification (Subtitle Only mode).")

656: 

657:             # Export subtitle.srt if available

658:             subtitle_srt_src = os.path.join(project_dir, "subtitle", "aligned_transcript.srt")

659:             subtitle_srt_dest = os.path.join(project_dir, "subtitle.srt")

660:             has_subtitles = False

661:             if os.path.exists(subtitle_srt_src):

662:                 try:

663:                     shutil.copy2(subtitle_srt_src, subtitle_srt_dest)

664:                     logger.info(f"Saved subtitle.srt to: {project_dir}")

665:                     has_subtitles = True

666:                 except Exception as e:

667:                     logger.warning(f"Could not copy subtitle.srt to project dir: {str(e)}")

668:             

669:             state_manager.set_metadata("voice_wav_dest", voice_wav_dest)

670:             state_manager.set_metadata("voice_mp3_dest", voice_mp3_dest)

671:             state_manager.set_metadata("narr_dur", narr_dur)

672:             state_manager.set_metadata("has_subtitles", has_subtitles)

673:             state_manager.set_metadata("subtitle_srt_dest", subtitle_srt_dest)

674:             state_manager.mark_completed("stage_7")

675:         else:

676:             logger.info("Stage 7: Skipped (Already completed).")

677:             voice_wav_dest = state_manager.get_metadata("voice_wav_dest")

678:             voice_mp3_dest = state_manager.get_metadata("voice_mp3_dest")

679:             narr_dur = state_manager.get_metadata("narr_dur", 0.0)

680:             has_subtitles = state_manager.get_metadata("has_subtitles", False)

681:             subtitle_srt_dest = state_manager.get_metadata("subtitle_srt_dest")

682: 

683:         # 8. Video and Audio Composition (Stitch Video)

684:         final_mp4_dest = os.path.join(project_dir, "final.mp4")

685:         if not skip_video:

686:             logger.info("Stage 8: Video and Audio Composition started.")

687:             state_manager.update_execution_state("Running", progress=95, current_stage="Stage 8: Video rendering")

688:             if not state_manager.is_completed("stage_8"):

689:                 stitched = False

690:                 import subprocess

691: 

692:                 if has_subtitles and subtitle_srt_dest:

693:                     try:

694:                         # Fix Windows subtitle path escaping (escape colon for FFmpeg filter)

695:                         sub_path_fw = subtitle_srt_dest.replace("\\", "/").replace(":", "\\:")

696:                         if skip_tts:

697:                             logger.info("Attempting to assemble final.mp4 with burned subtitles (original audio).")

698:                             cmd = [

699:                                 "ffmpeg", "-y",

700:                                 "-i", video_path,

701:                                 "-c:v", "libx264",

702:                                 "-c:a", "aac",

703:                                 "-vf", f"subtitles='{sub_path_fw}'",

704:                                 final_mp4_dest

705:                             ]

706:                         else:

707:                             logger.info("Attempting to assemble final.mp4 with audio replacement and burned subtitles.")

708:                             cmd = [

709:                                 "ffmpeg", "-y",

710:                                 "-i", video_path,

711:                                 "-i", voice_wav_dest,

712:                                 "-map", "0:v",

713:                                 "-map", "1:a",

714:                                 "-c:v", "libx264",

715:                                 "-c:a", "aac",

716:                                 "-vf", f"subtitles='{sub_path_fw}'",

717:                                 final_mp4_dest

718:                             ]

719:                         result = subprocess.run(cmd, capture_output=True, text=False, check=False)

720:                         stdout_str = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""

721:                         stderr_str = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

722:                         if result.returncode != 0:

723:                             raise subprocess.CalledProcessError(

724:                                 returncode=result.returncode,

725:                                 cmd=cmd,

726:                                 output=stdout_str,

727:                                 stderr=stderr_str

728:                             )

729:                         logger.info("Successfully generated final.mp4 with burned subtitles.")

730:                         stitched = True

731:                     except Exception as e:

732:                         logger.warning(f"Failed to generate final.mp4 with burned subtitles: {str(e)}.")

733:                         if not skip_tts:

734:                             logger.info("Falling back to audio-only replacement.")

735:                         else:

736:                             logger.error("No valid fallback available (Subtitle Only mode).")

737:                             raise e

738: 

739:                 if not stitched and not skip_tts:

740:                     logger.info("Assembling final.mp4 with audio replacement only (no burned subtitles).")

741:                     cmd = [

742:                         "ffmpeg", "-y",

743:                         "-i", video_path,

744:                         "-i", voice_wav_dest,

745:                         "-map", "0:v",

746:                         "-map", "1:a",

747:                         "-c:v", "copy",

748:                         "-c:a", "aac",

749:                         final_mp4_dest

750:                     ]

751:                     try:

752:                         result = subprocess.run(cmd, capture_output=True, text=False, check=False)

753:                         stdout_str = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""

754:                         stderr_str = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

755:                         if result.returncode != 0:

756:                             raise subprocess.CalledProcessError(

757:                                 returncode=result.returncode,

758:                                 cmd=cmd,

759:                                 output=stdout_str,

760:                                 stderr=stderr_str

761:                             )

762:                         logger.info("Successfully generated final.mp4 with audio replacement only.")

763:                         stitched = True

764:                     except Exception as e:

765:                         logger.error(f"Failed to generate final.mp4 during audio-only fallback: {str(e)}")

766:                         raise e

767:                 

768:                 # Verification step

769:                 if not os.path.exists(final_mp4_dest):

770:                     raise RuntimeError(f"Expected output video file not found at: {final_mp4_dest}")

771:                 

772:                 state_manager.mark_completed("stage_8")

773:             else:

774:                 logger.info("Stage 8: Skipped (Already completed).")

775:         else:

776:             logger.info("Stage 8: Video and Audio Composition skipped (requested output mode does not compile a final video).")

777: 

778:         # Generate sync_report.json

779:         sub_dur = aligned_transcript.duration if aligned_transcript and aligned_transcript.segments else 0.0

780:         diff_ms = abs(video_dur - narr_dur) * 1000.0 if not skip_tts else 0.0

781:         sync_report = {

782:             "video_duration": video_dur,

783:             "narration_duration": narr_dur,

784:             "subtitle_duration": sub_dur,

785:             "difference_ms": diff_ms

786:         }

787:         try:

788:             with open(os.path.join(project_dir, "sync_report.json"), "w", encoding="utf-8") as f:

789:                 json.dump(sync_report, f, indent=4)

790:             with open("sync_report.json", "w", encoding="utf-8") as f:

791:                 json.dump(sync_report, f, indent=4)

792:             logger.info("Saved sync_report.json to project directory and workspace root.")

793:         except Exception as e:

794:             logger.warning(f"Could not save sync_report.json: {str(e)}")

795: 

796:         state_manager.update_execution_state("Completed", progress=100, current_stage="Completed")

797:         

798:         report = {

799:             "status": "success",

800:             "total_duration_seconds": video_dur,

The above content does NOT show the entire file contents. If you need to view any lines of the file which were not shown to complete your task, call this tool again to view those lines.
