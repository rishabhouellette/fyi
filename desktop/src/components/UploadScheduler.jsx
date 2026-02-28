import React, { Suspense, useCallback, useRef, useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import UploadZone from './UploadZone';
import { deleteUpload } from '../lib/apiClient';

const SchedulerPro = React.lazy(() => import('./SchedulerPro'));

const UploadScheduler = () => {
  const { isDark } = useTheme();
  const [uploadedFileId, setUploadedFileId] = useState(null);
  const [uploadedItems, setUploadedItems] = useState([]);
  const [draft, setDraft] = useState({ title: '', caption: '' });

  const uploadActionsRef = useRef(null);

  // Keep useCallback imported to avoid churn; no scroll UX now (single merged flow).
  useCallback(() => {}, []);

  return (
    <div className="space-y-6">
      <UploadZone
        onUploadedFileIdChange={setUploadedFileId}
        onDraftChange={setDraft}
        onItemsChange={setUploadedItems}
        actionsRef={uploadActionsRef}
      />

      <Suspense
        fallback={
          <div className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}>
            <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Loading scheduling…</div>
          </div>
        }
      >
        <SchedulerPro
          embedded
          uploadedFileId={uploadedFileId}
          uploadedItems={uploadedItems}
          defaultTitle={draft?.title || ''}
          defaultCaption={draft?.caption || ''}
          onRemoveUploadedItem={async (item) => {
            const key = item?.key;
            const fileId = item?.uploadedFileId;

            // Best-effort: delete server-side upload to free disk.
            if (fileId) {
              try {
                await deleteUpload(fileId);
              } catch {
                // ignore (file may already be gone)
              }
            }
            try {
              uploadActionsRef.current?.removeItem?.(key);
            } catch {
              // ignore
            }
          }}
        />
      </Suspense>
    </div>
  );
};

export default UploadScheduler;
