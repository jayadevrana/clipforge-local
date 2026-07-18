import { JobDashboard } from "@/components/job-dashboard";

export default async function JobPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;

  return (
    <main className="grain-overlay min-h-screen px-6 py-8 sm:px-10">
      <div className="mx-auto max-w-7xl">
        <JobDashboard jobId={jobId} />
      </div>
    </main>
  );
}
