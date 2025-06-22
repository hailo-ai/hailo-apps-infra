/**
 * Copyright (c) 2021-2022 Hailo Technologies Ltd. All rights reserved.
 * Distributed under the LGPL license (https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt)
 **/

#include "tracker_update.hpp"
#include "hailo_common.hpp"

// This is a hack to remove the old classification from the tracker,
// We will be able to access the tracker from python.
// Don't use this file, it will be removed in the future.

void filter(HailoROIPtr roi)
{
    // Get all detection objects
    auto detections = roi->get_objects_typed(HAILO_DETECTION);
    // Get the tracker name (assume only one tracker)
    std::vector<std::string> tracker_names = HailoTracker::GetInstance().get_trackers_list();
    if (tracker_names.empty())
        return;
    const std::string &tracker_name = tracker_names[0];

    for (auto &detection : detections)
    {
        // Cast detection to HailoDetectionPtr
        auto detection_ptr = std::dynamic_pointer_cast<HailoDetection>(detection);
        if (!detection_ptr)
            continue;
        // Get tracking IDs for this detection
        auto unique_ids = detection_ptr->get_objects_typed(HAILO_UNIQUE_ID);
        if (unique_ids.empty())
            continue;
        auto unique_id_ptr = std::dynamic_pointer_cast<HailoUniqueID>(unique_ids[0]);
        if (!unique_id_ptr)
            continue;
        int track_id = unique_id_ptr->get_id();
        // Get all classifications for this detection
        auto classifications = detection_ptr->get_objects_typed(HAILO_CLASSIFICATION);
        if (!classifications.empty())
        {
            // Remove all classifications from the tracked object before adding new ones
            HailoTracker::GetInstance().remove_classifications_from_track(tracker_name, track_id, std::string("face_recon"));

            for (auto &classification : classifications)
            {
                // Cast to HailoClassificationPtr
                auto classification_ptr = std::dynamic_pointer_cast<HailoClassification>(classification);
                if (!classification_ptr)
                    continue;
                HailoTracker::GetInstance().add_object_to_track(tracker_name, track_id, classification);
                // std::cout << "Classification added to tracker: " << classification_ptr->get_label() << " track_id: " << track_id << std::endl;
            }
        }
    }
}
