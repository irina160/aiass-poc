export const UserSkeleton = () => {
    return (
        <div className="flex flex-row items-center gap-2">
            <div className=" rounded-full bg-slate-400 w-12 h-12 animate-pulse"></div>
            <div className="flex flex-col gap-2 items-end">
                <div className="w-[200px] h-4 bg-slate-400 rounded-md animate-pulse"></div>
                <div className="w-[100px] h-4 bg-slate-400 rounded-md animate-pulse"></div>
            </div>
        </div>
    );
};
