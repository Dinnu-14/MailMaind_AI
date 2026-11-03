import EmailList from "../components/EmailList";
import { PageHeader } from "../components/ui";
import { useApp } from "../context/AppContext";

export default function Inbox({ mode }: { mode: "priority" | "all" }) {
  const { stats, activeProfile } = useApp();
  return (
    <>
      <PageHeader
        title={mode === "priority" ? "Priority Inbox" : "All Inbox"}
        subtitle={mode === "priority"
          ? `Only emails relevant to the ${activeProfile?.name ?? ""} profile, each with the AI's reason. ${stats ? `${stats.important} of ${stats.total}.` : ""}`
          : "Every email, relevant or not. Nothing is ever deleted."} />
      <EmailList key={mode} mode={mode} />
    </>
  );
}
